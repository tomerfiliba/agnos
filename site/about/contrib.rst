.. _doc-contrib:

Contribution Guidelines
=======================

Disclaimer
----------
Agnos is developed by `IBM XIV <http://www.xivstorage.com>`_, 
and has been open-sourced for the benefit of other developers around the world.
We (IBM) would **greatly appreciate user-contributed code**, such as 
*bug fixes* or *features*, but as this project was first and foremost developed
for IBM's needs, it remains at our discretion whether patches or new features
get incorporated. This is actually not as draconic as it sounds -- it only 
means that control of the project is maintained by IBM; contributed code is 
likely to be accepted as long as it does not interfere with our general plans.

Being a large corporation, however, we have some legal concerns before 
accepting contributed code:

1. The code must be licensed under the Apache 2.0 license (or a weaker one, 
   such as BSD/MIT). For instance, we cannot accept code licensed under 
   the GPL.
2. The contributor must use the **sign-off procedure** (see below). It's a common
   practice in open source projects, which basically certifies you have the
   right to contribute the code. 

Other than that, contributed code should be meet our standards of code quality.
If the patch is only a few lines long, it is probably enough, but for 
larger patches, and especially for new features, it's important that they 
include proper documentation (be it in-code comments, updated site-material) 
and relevant unit tests. Code that does not meet these requirements might be 
turned down, although it's more likely that we will simply ask you to make 
some changes and resubmit. Also note that we reserve the right to make changes 
in contributed code, to make it meet our standards. 

**Proper credit will be given** in the `CONTRIBUTORS <http://github.com/tomerfiliba/agnos/blob/master/CONTRIBUTORS>`_
file (part of the repository), with your name, email and a short description of your work. 


Development
-----------
Project development takes place on `github <http://github.com/tomerfiliba/agnos>`_,
and our `issue tracker <http://github.com/tomerfiliba/agnos/issues>`_ is also
found there.

You are welcome to discuss development-related issues and other questions on our 
:ref:`mailing-list <doc-contact>`. However, it's **not** the place to report bugs
or submit patches. Please use the **issue tracker** to report bugs.

The preferred way to submit patches is by **forking**: you simply 
`fork <http://help.github.com/forking/>`_ our repository, apply your changes,
and submit us a `pull request <http://help.github.com/pull-requests>`_.
Normally we'd require patches to be submitted that way, as it's easiest for
us to manage, and has the added benefit of preserving your name in the commit.
However, very small patches (up to 10 LOC) may be email to the mailing list,
and we will take care of it from there.

We will notify you by email, within 30 days (at most), whether or not we 
chose to accept your patch.


Contribution License Agreement ("CLA")
--------------------------------------
When contributing code to the project, you must use the **sign-off procedure**.
It's a simple line at the end of the patch's description or commit message, 
which certifies that you wrote it or otherwise have the right to pass it on 
as an open-source patch.

.. note::
   You can use `git commit --signoff <http://www.kernel.org/pub/software/scm/git/docs/git-commit.html>`_,
   which automatically appends the relevant text to the commit message.

The rules are pretty simple::
    By making a contribution to this project, I certify that:
    (a) The contribution was created in whole or in part by me and I have the right to submit it under the 
    open source license indicated in the file; or
    (b) The contribution is based upon previous work that, to the best of my knowledge, is covered 
    under an appropriate open source License and I have the right under that license to submit that 
    work with modifications, whether created in whole or in part by me, under the same open source 
    license (unless I am permitted to submit under a different license), as indicated in the file; or
    (c) The contribution was provided directly to me by some other person who certified (a), (b) or (c) 
    and I have not modified it.
    (d) The contribution is made free of any other party's intellectual property claims or rights.
    (e) I understand and agree that this project and the contribution are public and that a record of 
    the contribution (including all personal information I submit with it, including my sign-off) 
    is maintained indefinitely and may be redistributed consistent with this project or the 
    open source license(s) involved.

Then you add a line saying ``Signed-off-by: Your Name <your@email.com>``




