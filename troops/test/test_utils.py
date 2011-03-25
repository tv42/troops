from nose.tools import (
    eq_ as eq,
    with_setup,
    )

import troops


def setup():
    # if this triggers, you're being silly and may suffer unit test
    # failures because of that
    assert not troops.hostname().endswith('.example.com')


def clear_roles():
    troops.roles.clear()
    troops.all_roles.clear()


def test_hostname():
    h = troops.hostname()
    # this is totally insufficient but i don't want to start regexp
    # matching arbitrary hostnames
    assert isinstance(h, str)


@with_setup(clear_roles)
def test_have_role_yes():
    troops.roles.add('foo')
    got = troops.have_role('foo')
    eq(got, True)


@with_setup(clear_roles)
def test_have_role_no():
    troops.roles.add('foo')
    got = troops.have_role('bar')
    eq(got, False)


@with_setup(clear_roles)
def test_define_role_simple():
    troops.define_role(
        'interactive',
        hosts=[
            'shellbox-1.example.com',
            'shellbox-2.example.com',
            ],
        )
    eq(
        troops.all_roles,
        dict(interactive=set([
                'shellbox-1.example.com',
                'shellbox-2.example.com',
                ])),
        )
    eq(troops.roles, set())


@with_setup(clear_roles)
def test_define_role_current():
    host = troops.hostname()
    assert host != 'notyou.example.com'
    troops.define_role(
        'good',
        hosts=[
            host,
            'notyou.example.com',
            ],
        )
    troops.define_role(
        'bad',
        hosts=[
            'notyou.example.com',
            ],
        )
    eq(
        sorted(troops.all_roles.keys()),
        sorted(['good', 'bad']),
        )
    eq(
        troops.all_roles['good'],
        set([
                host,
                'notyou.example.com',
                ]),
        )
    eq(
        troops.all_roles['bad'],
        set([
                'notyou.example.com',
                ]),
        )
    eq(troops.roles, set(['good']))


def test_deployable_simple():
    was_run = []

    def f():
        was_run.append(1)

    decorator = troops.deployable()
    g = decorator(f)
    assert g is f
    eq(was_run, [1])


def test_deployable_roles_no():
    was_run = []

    def f():
        was_run.append(1)

    decorator = troops.deployable(roles=['foo', 'bar'])
    g = decorator(f)
    assert g is f
    eq(was_run, [])


@with_setup(clear_roles)
def test_deployable_roles_yes():
    was_run = []

    def f():
        was_run.append(1)

    troops.roles.add('foo')
    decorator = troops.deployable(roles=['foo', 'bar'])
    g = decorator(f)
    assert g is f
    eq(was_run, [1])
