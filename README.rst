======================================
 Troops -- a software deployment tool
======================================

Troops is a reaction to Cfengine/BCFG2/Chef/Puppet. It is an explicit
attempt to build something different.

It is yet to be seen whether it's a viable approach.

See also Fabric (run commands over SSH, with actions/hosts/roles),
Kokki (which is a pretty close port of Chef to Python) and Poni (which
is something different, but it's as of yet unclear what).

Anti-goals
==========

Things Troops does **not** intend to achieve:

- centralization in any form
- bloat, required services such as message queues, databases, search
  engines
- crypto that is not SSH/GnuPG
- "uploading" code/data/cookbooks, that want to live in version
  control anyway
- slowness caused by latency and lack of parallelism, every node
  should act independently; think "pull you can push to"
- supporting every possible platform; especially, non-Linux servers
  seem just pointless at this time
- Ruby; that's been done enough already, and Homey just don't play
  that
- abstractions; adding a "recipe" will take as little code as feasible
- (weaker anti-goal): complete declarativeness; not doable without a
  custom language, and I'd rather not build that
- running shell commands over SSH; Troops will install the code
  required on the destination machine, giving you a powerful language
  to get things done
- doing things the same way as other deployment tools do it; the
  philosophy is "better or bust", not cloning features


Goals
=====

- cloud friendly; especially Debian/Ubuntu-style preseeding with
  EC2-style userdata, because that's what I use
- based on editing files & using version control; not Poni-style
  command line object manipulation
- support "green/blue deployment", roll out changes to a fraction of
  nodes first
- low learning curve (given sufficient background knowledge):
  "cookbooks" are just Python packages, code is just code you could
  run locally without Troops (TODO: reality check)
- (non-goal but strong bias:) nodes/sandboxes are discardable; it's
  easier to build a new one from scratch than to spend time handling
  uninstall etc cleanup
- a base design that is flexible, for example handling both push and
  pull deployments with the same logic


Your first deployment
=====================

Let's say you want to ensure all your machines always have ``tmux``
installed. Here's how you'd write that::

	from pydebianadmin import apt

	apt.install('tmux')

That's it! Running that bit of code will now install ``tmux``. Note
that ``pydebianadmin`` is just a completely generic utility library,
and isn't tied to Troops in any way. That is, Troops deployments are
just regular old Python. Now, how to get that to run on the desired
machines, we'll get back to that later.


Conditional deployment using roles
==================================

Now, you might have a bunch of machines where nobody ever logs in.
Let's install ``tmux`` only when the machine has the role
``interactive``::

	import troops

	from pydebianadmin import apt

	if troops.have_role('interactive'):
	    apt.install('tmux')

Now, when does a machine have that role? Exactly when you tell it to!
For example, if you want to use hostnames::

	import troops

	if troops.hostname().startswith('shellbox-'):
	    troops.roles.add('interactive')

Here, ``troops.hostname()`` is a convenience wrapper around
``socket.gethostname()`` that tries to get the fully qualified name.

You can also list out the machines that have a certain role::

	import troops

	troops.define_role(
	    'interactive',
	    hosts=[
	        'shellbox-1.example.com',
	        'shellbox-2.example.com',
	        ],
	    )

Organizing things into functions can help keep code organized. Any
functions defined with the decorator ``@deployable()`` will be
run. ``deployable`` can take a ``roles`` parameter to limit where the
function is called::

	import troops

	from pydebianadmin import apt

	@troops.deployable(roles=['interactive'])
	def tmux():
	    apt.install('tmux')


Remote deployment
=================

This is a trick section. Troops never deploys anything
remotely. Instead, we tell the remote machine what to do, and then the
remote machine does it "locally". Which, if you think of it, is
exactly what e.g. Fabric does, over SSH; Troops just shifts the focus
from "run this shell command" to "run this Python". And we let you use
whatever libraries are needed, so it feels more like actual
programming than writing a shell script inside Python.

To do this, we ship the deployment script (and auxiliary files, if
any) to the remote node, install the required dependencies, and just
run it.

Instead of reinventing the wheel and writing our own shipping
mechanism, we use Git for synchronizing changes. That also nicely
solves the problem of concurrent edits for us.

To make things more concrete: say you have a virtual machine with a
base Ubuntu install, and a user who can log in with SSH keys, with
``sudo`` access. Let's call it ``ubuntu@shellbox-1.example.com``.

Install ``troops`` on ``shellbox-1`` (TODO details, but it's just the
usual thing).

Let user ``ubuntu`` admin Troops on ``shellbox-1``::

	ssh ubuntu@shellbox-1 sudo gpasswd -a ubuntu troops

Set up a Git repository for the instructions on what to deploy (on
your local machine)::

	mkdir deploy
	cd deploy
	git init

Tell it what to deploy; add a file ``deploy.py`` with::

	import troops

	from pydebianadmin import apt

	troops.define_role(
	    'interactive',
	    hosts=[
	        'shellbox-1.example.com',
	        'shellbox-2.example.com',
	        ],
	    )

	@troops.deployable(roles=['interactive'])
	def tmux():
	    apt.install('tmux')

Next, list the dependencies the above code needs, in
``requirements.txt``, in `Pip format
<http://www.pip-installer.org/en/latest/requirement-format.html>`__
(Troops itself is installed automatically; you can list a versioned
dependency to ensure availability of certain utility functions)::

	PyDebianAdmin

You can also use ``requirements.txt`` to install specific versions or
forks of the dependencies, with the ``-e`` option. This is most useful
when you need to fix a bug in a dependency.

Next up, commit the above files to Git::

	git add deploy.py requirements.txt
	git commit -m 'Install tmux on interactive boxes.'

And ship them over to the remote machine::

	git push ubuntu@shellbox-1:/var/lib/troops/repo/main.git master

This will trigger a run, and the output of that will be shown to
you. This lets you do push-style deploys fairly nicely.


The pull deployment model
=========================

If you have lots of machines, push deployments get
frustrating. Thankfully, Troops handles pull deployments just as
nicely. To set this up, you need to host a Git repository somewhere.
For this example, we'll call that ``git@repos.example.com:deploy``.

If you are using SSH for connecting to the deploy repository, you need
to authorize the Troops installation on ``shellbox-1``; the SSH public
key is in ``/var/lib/troops/ssh/id_rsa.pub``.

To tell ``shellbox-1`` where to fetch from, run::

	ssh ubuntu@shellbox-1 git --git-dir=/var/lib/troops/repo/main.git \
	  remote add NAME git@repos.example.com:deploy

Replace ``NAME`` with whatever you consider descriptive.

Troops will try to fetch from *all* the defined remotes (when we said
no centralization, we meant it), and will update the local branch if
and only if a pure fast-forward merge can be done. Whenever the local
branch gets updated, Troops will run the deploy script.


Using Python C extensions
=========================

If you want to use Python C extensions that are not in the standard
library, and that depend on specific C libraries to build, you need to
make sure the right platform packages are installed before `Pip` can
install the package. Hence, ``requirements.txt`` is not sufficient.

For example ``lxml`` is a C extension that needs ``libxml2-dev`` and
``libxslt1-dev`` to compile. To do this, you need to write something
like this::

	import pip

	from pydebianadmin import apt

	apt.install('libxml2-dev', 'libxslt1-dev')
	pip.main(['install', '-e', 'lxml'])
	import lxml
	# now it should work


Coordinating multiple nodes
===========================

Let's say you're using one of those clouds that gives your nodes
static-but-random IP addresses. How do we tell node A how to reach
node B?

Or, even more critically, on initial deploy B creates a private/public
key pair. Or even just a plain old username/password. How do we
transmit this data to A, with maximum trust: no eavesdroppers, no
forgery.

First off, we need to understand and accept that we will not have this
information until B is up and running. Hence, we either need to delay
deploying A until we have all the information, or we need to deploy it
in some sort of degraded mode, where it will not depend on being able
to reach B. Or in case there's one A and lots of B1, B2, etc machines,
just not add Bn into A's configuration until Bn is up & ready.

This is fairly easy to solve for architectures where there's a
coordinating node that can communicate with both A and B. But Troops
is designed to be minimal, and there's no need to build such a
*centralization design smell* into Troops itself. Instead, we will
provide you enough rope to to implement it yourself.

Obviously, Troops itself got deployed somehow. This tends to take one
of two forms: 1. an "image", or a "seeded install" that is given
read-only information to consume, or 2. an SSH connection is used to
customize a "base image". Either way, it's easy to arrange a shell
accessible with an given SSH public key.

We can use that SSH trust relationship to directly handle the
exchange; a management node C can SSH to both B and A, and transmit
the necessary information. For the fully automated case, this would
need to be automated and triggered somehow by the creation of B (or
A). For now, let's look at the simpler manual way.

Let's say the deploy code for  B has::

	import subprocess

	subprocess.call([
	        'ssh-keygen',
	        '-N',  '',
	        '-f', '/srv/foo/ssh',
	        ])

Now, after deploying B, on our comfy local machine we trigger all the
deploys from, we can run::

	scp user@B:/srv/foo/ssh.pub B.pub
	scp B.pub user@A:/srv/foo/keys/B.pub

And then trigger the Troops on A to notice that the key is there::

	ssh user@A troops deploy

(TODO: the above is a rambly, edit for clarity)
