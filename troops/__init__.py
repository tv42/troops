import socket
import troops


roles = set()
all_roles = dict()


def hostname():
    return socket.gethostbyaddr(socket.gethostname())[0]


def have_role(role):
    return (role in troops.roles)


def define_role(role, hosts=[]):
    r = all_roles.setdefault(role, set())
    r.update(hosts)
    if hostname() in hosts:
        troops.roles.add(role)


def deployable(roles=None):
    run = False
    if roles is None:
        run = True
    else:
        roles = frozenset(roles)
        if roles & troops.roles:
            run = True

    def decorator(f):
        if run:
            f()
        return f
    return decorator
