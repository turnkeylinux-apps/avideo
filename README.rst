AVideo - Your own Tube website
==============================

AVideo_ is an open source solution that is freely available
to everyone. The idea came from the need to disseminate videos with
sensitive content using the internal, network infrastructure of an
institution. Soon the idea grew and took up space on the internet, as
an alternative to itself to replace, in a distributed way, the great
video sites like: YouTube, Vimeo, etc. With AVideo, you can create
your own video sharing site as well as stream live videos, always
inspired by the latest technologies. Among some of the features,
AVideo allows you to import and encode videos from other sites
directly from the Internet, as well as support for mobile devices,
through the responsive layout of the site or through a hybrid application
that allows you to directly view and stream videos of your phone.

This appliance includes all the standard features in `TurnKey Core`_,
and on top of that:

- AVideo 29.0 installed from the official tagged upstream source to
  /var/www/avideo.
- AVideo configured to support encoding, with AVideo Encoder 8.0 installed
  from the official tagged upstream source to /var/www/avideo-encoder.
- ``avideo-update`` provides a pinned release update path for both source
  checkouts and their database migrations.
- SSL support out of the box.
- `Adminer`_ administration frontend for MySQL (listening on port
  12322 - uses SSL).
- Postfix MTA (bound to localhost) to allow sending of email (e.g.,
  password recovery).
- Webmin modules for configuring Apache2, PHP, MySQL and Postfix.

Credentials *(passwords set at first boot)*
-------------------------------------------

-  Webmin, SSH, MySQL: username **root**
-  Adminer: username **adminer**
-  AVideo: username **admin**


.. _AVideo: https://platform.avideo.com/AVideo_OpenSource
.. _TurnKey Core: https://www.turnkeylinux.org/core
.. _Adminer: https://www.adminer.org/
