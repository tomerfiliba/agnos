.. _contribution_guidelines:

Contribution Guidelines
=======================
You are welcome to contribute code and submit patches to Agnos. However, 
as this project is being actively developed by IBM and used in its internal 
products, we cannot accept all code. For example, submitting a patch under the
GPL might "contaminate" the rest of the codebase, etc. Therefore, we require 
two things in order to accept third-party code:
# the contributed code or patch must be licensed under the **Apache License**
# you must comply with **sign-off procedure**

The *sign-off procedure* simply means that you add a line like so 
``Signed-off-by: Your Name <your@email.com>`` at the end of the description 
of your patch. It is used to certify that you have the rights to submit the code.
For more information, please refer to the :ref:`CLA <contribution_license_agreement>` below.
Code that does not meet the two rules above will be rejected on legal grounds.

Development
-----------
Agnos development takes place on `github <www.github.com>`_. Small patches 
(normally small bug fixes) may be sent by mail to `our mailing list <http://groups.google.com/group/agnos>`_
and we will process them. For new features or larger fixes, it's best to 
`fork <http://help.github.com/forking/>`_ our `git repository <http://github.com/tomerfiliba/agnos>`_,
do the changes, and click the `pull request <http://help.github.com/pull-requests>`_ button. 


.. _contribution_license_agreement:

Contribution License Agreement ("CLA")
--------------------------------------
The sign-off is a simple line at the end of the patch's description, 
which certifies that you wrote it or otherwise have the right to pass it on 
as an open-source patch. The rules are pretty simple::

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