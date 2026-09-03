WEBMIN_FW_TCP_INCOMING = 22 80 443 444 1935 8080 12321 12322

COMMON_OVERLAYS += 
COMMON_CONF += 

include $(FAB_PATH)/common/mk/turnkey/lamp.mk
include $(FAB_PATH)/common/mk/turnkey.mk
