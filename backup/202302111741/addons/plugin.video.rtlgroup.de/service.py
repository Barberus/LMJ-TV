# -*- coding: utf-8 -*-

import xbmcaddon

if __name__ == '__main__':
    xbmcaddon.Addon().setSetting('service_startWINDOW', 'true')
    xbmcaddon.Addon().setSetting('service_startWIDEVINE', 'true')
    xbmcaddon.Addon().setSetting('maximum_tries', '0')
