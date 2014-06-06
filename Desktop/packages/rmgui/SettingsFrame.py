import packages.rmnetwork as network
import packages.rmutil as rmutil
from packages.rmgui import *
from packages.rmnetwork.constants import *
import os, sys, platform, ast, time, threading, shutil

import wx
from wx.lib.pubsub import pub as Publisher
from wx.lib.wordwrap import wordwrap

################################################################################
# SETTINGS FRAME ###############################################################
################################################################################
class SettingsFrame(wx.Frame):
    def __init__(self,parent,id,title,host,config):
        wx.Frame.__init__(self,parent,id,title,size=(400,300))
        self.parent = parent
        self.Bind(wx.EVT_CLOSE, self.Close)
        self.host = host['addr']
        self.name = host['name']
        self.prgDialog = None
        self.Initialize()
        self.SetSizerAndFit(self.configSizer)
        self.Show()
        self.UpdateUI(config, True)

    def Close(self, event=None):
        Publisher.unsubAll()
        self.parent.SettingsClosedWithConfig(self.config)
        self.Destroy()

    def Initialize(self):
        self.configSizer = wx.GridBagSizer()
        # checkboxes
        self.cbImgEnabled = wx.CheckBox(self, -1, "Enable Images")
        self.cbVidEnabled = wx.CheckBox(self, -1, "Enable Videos")
        self.cbAutoplay = wx.CheckBox(self, -1, "Autoplay")
        self.cbRepeat = wx.CheckBox(self, -1, "Repeat")

        # interval, player name and ip
        intervalLabel = wx.StaticText(self,-1,label="Image interval:")
        self.imgIntervalLabel = wx.StaticText(self,-1,label="")
        nameLabel = wx.StaticText(self,-1,label="Player name:")
        self.playerNameLabel = wx.StaticText(self,-1,label="")
        addrLabel = wx.StaticText(self,-1,label="IP-Address:")
        playerAddr = wx.StaticText(self,-1,label=self.host)

        updateBtn = wx.Button(self, -1, "Update player")

        self.editInterval = wx.Button(self,-1,label="...",size=(27,25))
        self.editName = wx.Button(self,-1,label="...",size=(27,25))

        # horizontal divider line
        line = wx.StaticLine(self,-1,size=(260,2))

        # set names for further identifying
        self.cbImgEnabled.SetName('image_enabled')
        self.cbVidEnabled.SetName('video_enabled')
        self.cbAutoplay.SetName('autoplay')
        self.cbRepeat.SetName('repeat')
        self.editInterval.SetName('btn_image_interval')
        self.editName.SetName('btn_player_name')
        updateBtn.SetName('btn_update')

        # bind UI element events
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbImgEnabled)
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbVidEnabled)
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbAutoplay)
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbRepeat)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, self.editInterval)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, self.editName)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, updateBtn)

        self.configSizer.Add(self.cbImgEnabled, (0,0), flag=wx.TOP | wx.LEFT, border = 5)
        self.configSizer.Add(self.cbVidEnabled, (1,0), flag=wx.LEFT, border = 5)
        self.configSizer.Add(self.cbAutoplay, (0,1), flag=wx.TOP, border = 5)
        self.configSizer.Add(self.cbRepeat, (1,1))
        self.configSizer.Add(intervalLabel, (3,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        self.configSizer.Add(self.imgIntervalLabel, (3,1), flag=wx.ALIGN_CENTER_VERTICAL)
        self.configSizer.Add(self.editInterval, (3,3))
        self.configSizer.Add(nameLabel, (4,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        self.configSizer.Add(self.playerNameLabel, (4,1), flag=wx.ALIGN_CENTER_VERTICAL)
        self.configSizer.Add(self.editName, (4,3))
        self.configSizer.Add(addrLabel, (5,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.BOTTOM, border = 5)
        self.configSizer.Add(playerAddr, (5,1), flag = wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, border = 5)
        self.configSizer.Add(updateBtn, (0,4), flag = wx.ALL, border = 5)
        self.configSizer.Add(line, (2,0), span=(1,5), flag=wx.TOP | wx.BOTTOM, border=5)


    def UpdateUI(self, config, isDict=False):
        if isDict:
            configDict = config
        else:
            configDict = ast.literal_eval(config)
        self.config = configDict
        self.cbImgEnabled.SetValue(configDict['image_enabled'])
        self.cbVidEnabled.SetValue(configDict['video_enabled'])
        self.cbRepeat.SetValue(configDict['repeat'])
        self.cbAutoplay.SetValue(configDict['autoplay'])
        self.imgIntervalLabel.SetLabel(str(configDict['image_interval']))
        self.playerNameLabel.SetLabel(str(configDict['player_name']))

    def LoadConfig(self):
        Publisher.subscribe(self.UpdateUI, 'config')
        Publisher.subscribe(self.UdpListenerStopped, 'listener_stop')
        print "Observers registered..."
        msgData = network.messages.getMessage(CONFIG_REQUEST)
        dlgStyle =  wx.PD_AUTO_HIDE
        #self.prgDialog = wx.ProgressDialog("Loading...", "Loading configuration from player...", maximum = 0, parent = self, style = dlgStyle)
        #self.prgDialog.Pulse()
        network.udpconnector.sendMessage(msgData, self.host)

    def UdpListenerStopped(self):
        if self.prgDialog:
            self.prgDialog.Update(100)
            self.prgDialog.Destroy()
            #self.prgDialog = None

    def ButtonClicked(self, event):
        button = event.GetEventObject()
        if button.GetName() == 'btn_image_interval':
            dlg = wx.TextEntryDialog(self, "New Interval:", "Image Interval", self.imgIntervalLabel.GetLabel())
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    newInterval = int(dlg.GetValue())
                    # self.imgIntervalLabel.SetLabel(str(newInterval))
                    msgData = network.messages.getConfigUpdateMessage("image_interval", newInterval)
                    network.udpconnector.sendMessage(msgData, self.host)
                    time.sleep(0.2)
                    self.LoadConfig()
                except Exception, e:
                    error = wx.MessageDialog(self, "Please enter a valid number!", "Invalid interval", wx.OK | wx.ICON_EXCLAMATION)
                    error.ShowModal()

            dlg.Destroy()
        elif button.GetName() == 'btn_player_name':
            dlg = wx.TextEntryDialog(self, "New name:", "Player Name", self.playerNameLabel.GetLabel())
            if dlg.ShowModal() == wx.ID_OK:
                newName = dlg.GetValue()
                self.playerNameLabel.SetLabel(newName)
                msgData = network.messages.getConfigUpdateMessage("player_name", str(newName))
                network.udpconnector.sendMessage(msgData, self.host)
                time.sleep(0.2)
                self.LoadConfig()
            dlg.Destroy()
        elif button.GetName() == 'btn_update':
            # register observer
            network.udpresponselistener.registerObserver([OBS_UPDATE, self.OnPlayerUpdated])
            network.udpresponselistener.registerObserver([OBS_STOP, self.UdpListenerStopped])

            self.prgDialog = wx.ProgressDialog("Updating...", "Player is trying to update, please stand by...")
            #self.prgDialog.ShowModal()
            self.prgDialog.Pulse()

            msgData = network.messages.getMessage(PLAYER_UPDATE)
            network.udpconnector.sendMessage(msgData, self.host, UDP_UPDATE_TIMEOUT)

    def CheckboxToggled(self, event):
        checkbox = event.GetEventObject()
        print checkbox.GetName()
        msgData = network.messages.getConfigUpdateMessage(checkbox.GetName(), checkbox.IsChecked())
        network.udpconnector.sendMessage(msgData, self.host)
        self.LoadConfig()