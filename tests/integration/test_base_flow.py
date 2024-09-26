import os
import copy

import pytest

from minds.client import Client

from minds.datasources.examples import example_ds

from minds.exceptions import ObjectNotFound


@pytest.fixture(scope="module")
def client():
    api_key = os.getenv('API_KEY')
    if api_key is None:
        raise RuntimeError('Environment variable API_KEY is not set')

    base_url = 'https://dev.mindsdb.com'
    return Client(api_key, base_url=base_url)


def test_wrong_api_key():
    base_url = 'https://dev.mindsdb.com'
    client = Client('api_key', base_url=base_url)
    with pytest.raises(Exception):
        client.datasources.get('example_db')


def test_datasources(client):

    # remove previous object
    try:
        client.datasources.drop(example_ds.name)
    except ObjectNotFound:
        ...

    # create
    ds = client.datasources.create(example_ds)
    ds = client.datasources.create(example_ds, replace=True)
    assert ds.name == example_ds.name

    # get
    ds = client.datasources.get(example_ds.name)

    # list
    ds_list = client.datasources.list()
    assert len(ds_list) > 0

    # drop
    client.datasources.drop(ds.name)


def test_minds(client):
    ds_name = 'test_datasource_'
    ds_name2 = 'test_datasource2_'
    mind_name = 'int_test_mind_'
    mind_name2 = 'int_test_mind2_'
    prompt1 = 'answer in german'
    prompt2 = 'answer in spanish'

    # remove previous objects
    for name in (mind_name, mind_name2):
        try:
            client.minds.drop(name)
        except ObjectNotFound:
            ...

    # prepare datasources
    ds_cfg = copy.copy(example_ds)
    ds_cfg.name = ds_name
    ds = client.datasources.create(example_ds, replace=True)

    # second datasource
    ds2_cfg = copy.copy(example_ds)
    ds2_cfg.name = ds_name2

    # create
    mind = client.minds.create(
        mind_name,
        datasources=[ds],
        provider='openai'
    )
    mind = client.minds.create(
        mind_name,
        replace=True,
        datasources=[ds.name, ds2_cfg],
        parameters={
            'prompt_template': prompt1
        }
    )

    # get
    mind = client.minds.get(mind_name)
    assert len(mind.datasources) == 2
    assert mind.parameters['prompt_template'] == prompt1

    # list
    mind_list = client.minds.list()
    assert len(mind_list) > 0

    # rename & update
    mind.update(
        name=mind_name2,
        datasources=[ds.name],
        parameters={
            'prompt_template': prompt2
        }
    )
    with pytest.raises(ObjectNotFound):
        # this name not exists
        client.minds.get(mind_name)

    mind = client.minds.get(mind_name2)
    assert len(mind.datasources) == 1
    assert mind.parameters['prompt_template'] == prompt2

    # add datasource
    mind.add_datasource(ds2_cfg)
    assert len(mind.datasources) == 2

    # del datasource
    mind.del_datasource(ds2_cfg.name)
    assert len(mind.datasources) == 1

    # completion
    answer = mind.completion('say hello')
    assert 'hola' in answer.lower()
    # stream completion
    success = False
    for chunk in mind.completion('say hello', stream=True):
        if 'hola' in chunk.content.lower():
            success = True
    assert success is True

    # drop
    client.minds.drop(mind_name2)
    client.datasources.drop(ds.name)
    client.datasources.drop(ds2_cfg.name)
