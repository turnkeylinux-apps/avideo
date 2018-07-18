WEBMIN_FW_TCP_INCOMING = 22 80 81 443 444 1935 12320 12321

COMMON_OVERLAYS += 
COMMON_CONF += 

include $(FAB_PATH)/common/mk/turnkey/lamp.mk
include $(FAB_PATH)/common/mk/turnkey.mk
