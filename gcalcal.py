#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from xml.dom import minidom
import codecs
import base64
import subprocess
import calendar
import datetime
from datetime import datetime, date, timedelta
from os.path import abspath, dirname, join

WHERE_AM_I = abspath(dirname(__file__))
GCAL_PATH="~/.local/bin"
EVENT_CALENDAR="kaoru.konno@gmail.com"
HOLIDAY_CALENDAR="日本の祝日"

class ConfigXML:
    OptionList = {   "x_pos":"40",
                     "y_pos":"40",
                     "width":"320",
                     "height":"200",
                     "opacity":"100%",
                     "decoration":"True",
                     "gcal_path":"",
                     "event_calendar":"xxx@gmail.com",
                     "holiday_calendar":"日本の祝日",
                     "mdColor":"#FFFF00",
                     "tmColor":"#80FF80",
                     "textColor":"#FFFFFF",
    }
    AppName = "Gcalcal"
    ConfigPath = "/.config/Gcalcal.xml"
    Options = {}    #オプション値の辞書
    domobj = None

    def __init__(self, read):
        #print "ConfigXML"
        if read == True:
            try:
                self.domobj = minidom.parse(os.path.abspath(os.path.expanduser("~") + self.ConfigPath))
                options = self.domobj.getElementsByTagName("options")
                for opt in options :
                    for op,defVal in self.OptionList.items():
                        elm = opt.getElementsByTagName(op)
                        if len(elm) > 0 :
                            self.Options[op] = self.getText(elm[0].childNodes)
                        else:
                            self.Options[op] = defVal
            except Exception as e:
                print(e)
                for op,defVal in self.OptionList.items():
                    self.Options[op] = defVal

    def getText(self,nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                text = str(node.data)
                text = text.rstrip(" \t\n")
                text = text.lstrip(" \t\n")
                rc = rc + text
        return rc

    def GetOption(self, optName ):
        if optName == "password":
            return str(base64.b64decode(self.Options[optName]))
        else:
            try:
                return str(self.Options[optName])
            except:
                return str(self.OptionList[optName])

    def SetOption(self, optName, value ):
        if optName == "password":
            val = base64.b64encode(value)
            self.Options[optName] = val
        else:
            self.Options[optName] = value

    def Write(self):
        try:
            impl = minidom.getDOMImplementation()
            newdoc = impl.createDocument(None, self.AppName, None)
            root = newdoc.documentElement
            opts = newdoc.createElement("options")
            root.appendChild(opts)
            for op in self.OptionList.keys():
                opt = newdoc.createElement(op)
                opts.appendChild(opt)
                text = newdoc.createTextNode(str(self.Options[op]))
                opt.appendChild(text)
            file = codecs.open(os.path.abspath(os.path.expanduser("~") + self.ConfigPath), 'wb', encoding='utf-8')
            newdoc.writexml(file, '', '\t', '\n', encoding='utf-8')
        except:
            print ("Error Config Write")

class myCalendar:
    """[summary]
    カレンダークラス
    Returns:
        [type] -- [description]
    """

    def __init__(self):
        """[summary]
        初期化
        """

        global GCAL_PATH
        global EVENT_CALENDAR
        global HOLIDAY_CALENDAR
        conf = ConfigXML(True)
        #メインウィンドウを作成
        self.wMain = Gtk.Builder()
        self.wMain.add_from_file(os.path.dirname(os.path.abspath(__file__)) + "/gcalcal.glade")
        self.context_menu =  self.wMain.get_object ("mMenu")
        self.mainWindow = self.wMain.get_object ("wCalendar")
        self.calCalendar = self.wMain.get_object ("calCalendar")
        self.txtBuffer = self.wMain.get_object ("txtInfoBuffer")
        self.schedule = self.wMain.get_object ("txtInfoText")
        self.lblMonth = self.wMain.get_object ("lblMonth")
        self.lblYear = self.wMain.get_object ("lblYear")
        self.cmbMonth = self.wMain.get_object ("cmbMonth")
        self.cmbYear = self.wMain.get_object ("cmbYear")
        for month_name in calendar.month_name[1:]:
            self.cmbMonth.append(None, month_name)
        self.cmbMonth.set_active(date.today().month - 1)
        for y in range(-5, 5):
            self.cmbYear.append(str(date.today().year + y), str(date.today().year + y))
        self.cmbYear.set_active_id(str(date.today().year))
        lblNo = 0
        self.days = [[0 for i in range(7)] for j in range(7)]
        for row in range(6):
            for col in range(7):
                self.days[row][col] = self.wMain.get_object ("lbl{:02d}".format(lblNo))
                self.wMain.get_object("ev{:02d}".format(lblNo)).connect("button_release_event", self.on_day_button_release_event)
                lblNo += 1
        # 設定ダイアログ
        self.settingDialog = self.wMain.get_object ("dlgSetting")
        self.btnSettingOK = self.wMain.get_object("btnSettingOK")
        self.btnSettingCancel = self.wMain.get_object("btnSettingCancel")
        self.btnFileChoose = self.wMain.get_object ("btnFileChoose")
        self.txtEventCalendar = self.wMain.get_object ("txtEventCalendar")
        self.txtHolidayCalendar = self.wMain.get_object ("txtHolidayCalendar")
        self.sclOpecity = self.wMain.get_object ("sclOpecity")
        self.btnMDColor = self.wMain.get_object ("btnMDColor")
        self.btnTMColor = self.wMain.get_object ("btnTMColor")
        self.btnTextColor = self.wMain.get_object ("btnTextColor")
        # GdkColormap to GdkVisual
        # なんか透過ウィンドウを作成するのはこれがミソっぽい
        screen = self.mainWindow.get_screen()
        visual = screen.get_rgba_visual()
        if visual != None and screen.is_composited():
            self.mainWindow.set_visual(visual)
        else:
            print ("no Composited...")
        dic = {
            "on_miExit_activate" : self.on_miExit_activate,
            "on_miSetting_activate" : self.on_miSetting_activate,
            "on_wCalendar_destroy" : self.on_wCalendar_destroy,
            "on_wCalendar_button_press_event" : self.on_wCalendar_button_press_event,
            "on_wCalendar_realize" : self.on_MainWindow_realize,
            "on_miTitlebar_toggled" : self.on_miTitlebar_toggled,
            "on_mi010_activate" : self.on_miOpacity_activate,
            "on_mi020_activate" : self.on_miOpacity_activate,
            "on_mi030_activate" : self.on_miOpacity_activate,
            "on_mi040_activate" : self.on_miOpacity_activate,
            "on_mi050_activate" : self.on_miOpacity_activate,
            "on_mi060_activate" : self.on_miOpacity_activate,
            "on_mi070_activate" : self.on_miOpacity_activate,
            "on_mi080_activate" : self.on_miOpacity_activate,
            "on_mi090_activate" : self.on_miOpacity_activate,
            "on_mi100_activate" : self.on_miOpacity_activate,
            "on_wCalendar_focus_out_event": self.on_wCalendar_focus_out_event,
            "on_evMonthDown_button_release_event": self.on_evMonthDown_button_release_event,
            "on_evMonthUp_button_release_event": self.on_evMonthUp_button_release_event,
            "on_evYearDonw_button_release_event": self.on_evYearDonw_button_release_event,
            "on_evYearUp_button_release_event": self.on_evYearUp_button_release_event,
            "on_evMonth_button_press_event": self.on_evMonth_button_press_event,
            "on_evYear_button_press_event": self.on_evYear_button_press_event,
            "on_cmbMonth_changed": self.on_cmbMonth_changed,
            "on_cmbYear_changed": self.on_cmbYear_changed,
            "on_btnSettingOK_clicked": self.on_btnSettingOK_clicked,
            "on_btnSettingCancel_clicked": self.on_btnSettingCancel_clicked,
        }
        self.wMain.connect_signals(dic)
        xpos = conf.GetOption("x_pos")
        ypos = conf.GetOption("y_pos")
        self.w = int(conf.GetOption("width"))
        self.h = int(conf.GetOption("height"))
        self.decoration = eval(conf.GetOption("decoration"))
        GCAL_PATH = conf.GetOption("gcal_path")
        EVENT_CALENDAR = conf.GetOption("event_calendar")
        HOLIDAY_CALENDAR = conf.GetOption("holiday_calendar")
        self.btnMDColor.set_color(Gdk.color_parse(conf.GetOption("mdColor")))
        self.btnTMColor.set_color(Gdk.color_parse(conf.GetOption("tmColor")))
        self.btnTextColor.set_color(Gdk.color_parse(conf.GetOption("textColor")))
        self.mainWindow.move(int(xpos), int(ypos))
        self.cancalEvent = True
        self.mainWindow.resize(self.w,self.h)
        self.wMain.get_object("miTitlebar").set_active(self.decoration)
        self.cancalEvent = False
        self.opacity = float(conf.GetOption("opacity").replace("%","")) / 100
        self.sclOpecity.set_value(self.opacity * 100)
        self.mainWindow.set_opacity(self.opacity)
        self.schedule.set_opacity(self.opacity)
        self.mainWindow.set_decorated(self.decoration)
        now = date.today()
        self.month = now.month
        self.year = now.year
        self.set_style()
        self.makeCalendar(now.year, now.month)
        self.mainWindow.show_all()

    def makeCalendar(self,year,month):
        '''[summary]
        カレンダー生成
        Arguments:
            year {[int]} -- [カレンダーの年]
            month {[int]} -- [カレンダーの月]
        '''
        self.initDayStyle()
        calendar.setfirstweekday(calendar.SUNDAY)
        self.lblMonth.set_text(calendar.month_name[month])
        self.lblYear.set_text(str(year))
        cal = calendar.monthcalendar(year, month)
        firstWeek, lastday = calendar.monthrange(year,month)
        prevdate = date(year,month,1) - timedelta(days=1)
        nextdate = date(year,month,lastday) + timedelta(days=1)
        prevcal = calendar.monthcalendar(prevdate.year, prevdate.month)
        nextcal = calendar.monthcalendar(nextdate.year, nextdate.month)
        start = 0
        if firstWeek == 6:
            start = 1
        calRow = 0
        for row in range(start, 6):
            for col in range(7):
                if cal[calRow][col] != 0:
                    self.days[row][col].set_text(str(cal[calRow][col]))
                    if date.today() == date(year, month, cal[calRow][col]):
                        css_context = self.days[row][col].get_style_context()
                        css_context.add_class("today")
            calRow += 1
            if len(cal) <= calRow:
                break
        # 前月
        prevLastRow = len(prevcal)
        for col in range(7):
            if prevcal[prevLastRow - 1][col] != 0:
                self.days[0][col].set_text(str(prevcal[prevLastRow - 1][col]))
                css_context = self.days[0][col].get_style_context()
                css_context.add_class("prev_month")
        # 次月
        lastrow = len(cal) - 1 + start
        start = 0
        if firstWeek != 6:
            start = 1
        for row in range(6 - len(cal) + start):
            for col in range(7):
                if nextcal[row][col] != 0:
                    self.days[lastrow+row][col].set_text(str(nextcal[row][col]))
                    css_context = self.days[lastrow+row][col].get_style_context()
                    css_context.add_class("next_month")
        self.setEventDay()
        self.setEventDayList()
        self.setHolidayList()
        
    def initDayStyle(self):
        """[summary]
        カレンダー属性初期化
        """
        for row in range(6):
            for col in range(7):
                self.days[row][col].set_has_tooltip(False)
                css_context = self.days[row][col].get_style_context()
                css_context.remove_class("today")
                css_context.remove_class("holiday")
                css_context.remove_class("prev_month")
                css_context.remove_class("next_month")
                css_context.remove_class("selected")
                css_context.remove_class("marked")

    def findDayLabel(self, day):
        """[summary]
        指定日のカレンダーラベルコントロールの取得
        Arguments:
            day {[type]} -- [description]
        
        Returns:
            [Gtk.Label] -- [指定日のラベルコントロール]
        """
        for row in range(6):
            for col in range(7):
                css_context = self.days[row][col].get_style_context()
                if css_context.has_class("prev_month") == False and css_context.has_class("next_month") == False:
                    if int(self.days[row][col].get_text()) == day:
                        return self.days[row][col]
        return None

    def tooltip_callback(self, widget, x, y, keyboard_mode, tooltip):
        """[summary]
        ツールチップ表示コールバック
        Arguments:
            widget {[type]} -- [description]
            x {[type]} -- [description]
            y {[type]} -- [description]
            keyboard_mode {[type]} -- [description]
            tooltip {[type]} -- [description]
        
        Returns:
            [bool] -- [True：表示/False：非表示]]
        """
        text = widget.get_tooltip_text()
        tooltip.set_text(text)
        return True

    def setHoliday(self, day, text):
        """[summary]
        祝日設定
        Arguments:
            day {[type]} -- [description]
            text {[type]} -- [description]
        """
        day = self.findDayLabel(day)
        css_context = day.get_style_context()
        css_context.add_class("holiday")
        day.set_has_tooltip(True)
        day.set_tooltip_text(text)
        day.connect("query-tooltip", self.tooltip_callback)


    def setMarked(self, day, text):
        """[summary]
        マーク指定
        Arguments:
            day {[type]} -- [description]
            text {[type]} -- [description]
        """
        day = self.findDayLabel(day)
        css_context = day.get_style_context()
        if css_context.has_class("marked"):
            tooltip = day.get_tooltip_text()
            tooltip += "\n" + text
            day.set_tooltip_text(tooltip)
        else:
            css_context.add_class("marked")
            day.set_has_tooltip(True)
            day.set_tooltip_text(text)
            day.connect("query-tooltip", self.tooltip_callback)

    def on_evMonthDown_button_release_event(self, wdget, event):
        """[summary]
        前月ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        prevdate = date(self.year,self.month,1) - timedelta(days=1)
        self.month = prevdate.month
        self.year = prevdate.year
        self.makeCalendar(self.year, self.month)
        return

    def on_evMonthUp_button_release_event(self, wdget, event):
        """[summary]
        次月ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        firstWeek, lastday = calendar.monthrange(self.year, self.month)
        nextdate = date(self.year,self.month,lastday) + timedelta(days=1)
        self.month = nextdate.month
        self.year = nextdate.year
        self.makeCalendar(self.year, self.month)
        return

    def on_evYearDonw_button_release_event(self, wdget, event):
        """[summary]
        前年ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        self.year -= 1
        self.makeCalendar(self.year, self.month)
        return

    def on_evYearUp_button_release_event(self, wdget, event):
        """[summary]
        次年ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        self.year += 1
        self.makeCalendar(self.year, self.month)
        return

    def on_day_button_release_event(self, widget, event):
        """[summary]
        日付ラベルクリックイベント
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        day = widget.get_child()
        if day != None:
            css_context = day.get_style_context()
            if css_context.has_class("prev_month"):
                self.on_evMonthDown_button_release_event(widget, event)
            if css_context.has_class("next_month"):
                self.on_evMonthUp_button_release_event(widget, event)
        return

    def on_wCalendar_button_press_event(self,widget,event):
        """[summary]
        メインウィンドウ上でのマウスボタンクリックイベント
        右クリックメニューの表示
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            #右クリック
            self.context_menu.popup(None, None, None,None, event.button, event.time)

    def on_miTitlebar_toggled(self, widget):
        """[summary]
        タイトルバーを表示メニューイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        if self.cancalEvent == True:
            return
        self.decoration = widget.get_active()
        self.mainWindow.set_decorated(self.decoration)
        return

    def on_miOpacity_activate(self, widget):
        """[summary]
        透明度指定メニューイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        menuStr = widget.get_child().get_text()
        self.opacity = float(menuStr.replace("%","")) / 100
        self.mainWindow.set_opacity(self.opacity)
        self.schedule.set_opacity(self.opacity)
        return

    def on_evMonth_button_press_event(self, widget,event):
        """[summary]
        月ラベルマウスボタンクリックイベント
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        if self.cmbMonth.get_no_show_all() == True:
            self.cmbMonth.set_no_show_all(False)
            self.cmbYear.set_no_show_all(False)
            self.mainWindow.show_all()
        else:
            self.cmbMonth.set_no_show_all(True)
            self.cmbYear.set_no_show_all(True)
            self.cmbMonth.hide()
            self.cmbYear.hide()
            self.mainWindow.show_all()
        return

    def on_evYear_button_press_event(self, widget,event):
        """[summary]
        年ラベルマウスボタンクリックイベント
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        if self.cmbYear.get_no_show_all() == True:
            self.cmbMonth.set_no_show_all(False)
            self.cmbYear.set_no_show_all(False)
            self.mainWindow.show_all()
        else:
            self.cmbMonth.set_no_show_all(True)
            self.cmbYear.set_no_show_all(True)
            self.cmbMonth.hide()
            self.cmbYear.hide()
            self.mainWindow.show_all()
        return
        
    def on_cmbMonth_changed(self, widget):
        """[summary]
        月コンボボックス選択イベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(True)
        self.cmbYear.set_no_show_all(True)
        self.cmbMonth.hide()
        self.cmbYear.hide()
        self.mainWindow.show_all()
        self.month = self.cmbMonth.get_active() + 1
        self.makeCalendar(self.year, self.month)
        return
        
    def on_cmbYear_changed(self, widget):
        """[summary]
        年コンボボックスイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(True)
        self.cmbYear.set_no_show_all(True)
        self.cmbMonth.hide()
        self.cmbYear.hide()
        self.mainWindow.show_all()
        self.year = int(self.cmbYear.get_active_text())
        self.makeCalendar(self.year, self.month)
        return

    def _saveConf(self):
        """[summary]
        設定保存
        """
        global GCAL_PATH
        global EVENT_CALENDAR
        global HOLIDAY_CALENDAR
        conf = ConfigXML(False)
        (xpos, ypos) = self.mainWindow.get_position()
        (self.w, self.h) = self.mainWindow.get_size()
        if len(GCAL_PATH) > 0:
            GCAL_PATH = os.path.join(GCAL_PATH, '', '')
        conf.SetOption("x_pos",xpos)
        conf.SetOption("y_pos",ypos)
        conf.SetOption("width",self.w)
        conf.SetOption("height",self.h)
        conf.SetOption("opacity",str(self.opacity*100) + "%")
        conf.SetOption("decoration",str(self.decoration))
        conf.SetOption("gcal_path", GCAL_PATH)
        conf.SetOption("event_calendar", EVENT_CALENDAR)
        conf.SetOption("holiday_calendar", HOLIDAY_CALENDAR)
        conf.SetOption("mdColor", self.btnMDColor.get_color().to_string())
        conf.SetOption("tmColor",self.btnTMColor.get_color().to_string())
        conf.SetOption("textColor",self.btnTextColor.get_color().to_string())
        conf.Write()

    def on_MainWindow_realize(self, widget):
        """[summary]
        メインウィンドウ表示イベント
        設定値を保存する
        Arguments:
            widget {[type]} -- [description]
        """
        if self.cancalEvent == True:
            return
        self._saveConf()
        return

    def on_wCalendar_focus_out_event(self, widget, event):
        """[summary]
        メインウィンドウフォーカスアウトイベント
        設定値を保存する
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        if self.cancalEvent == True:
            return
        self._saveConf()
        self.cancalEvent = False
        return

    def setEventDay(self):
        """[summary]
        gcalcliから取得したイベントをカレンダーに設定
        """
        if len(EVENT_CALENDAR) == 0:
            return
        montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli " + "--calendar \"" + EVENT_CALENDAR + "\" --nocolor agenda --tsv " + montStart.isoformat() + " " + montFinish.isoformat())
        day = 0
        for sch in schedules:
            if len(sch) > 0 and sch != "No Events Found...":
                info = sch.split("\t")
                day = datetime.strptime(info[0], "%Y-%m-%d")
                self.setMarked(day.day, info[1] + " " + " ".join(info[4:]))
    
    def setEventDayList(self):
        """[summary]
        gcalcliから取得したイベント情報をTextViewに設定
        """
        montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli --nocolor agenda --tsv " + montStart.isoformat() + " " + montFinish.isoformat())
        self.txtBuffer.set_text("")
        textIter = self.txtBuffer.get_start_iter()
        for sch in schedules:
            if len(sch) > 0:
                info = sch.split("\t")
                day = datetime.strptime(info[0], "%Y-%m-%d")
                self.txtBuffer.insert_markup(textIter, "<span foreground='" + self.btnMDColor.get_color().to_string() + "'>" + "{:02d}/{:02d}".format(day.month,day.day) + "</span> ",-1)
                textIter = self.txtBuffer.get_end_iter()
                self.txtBuffer.insert_markup(textIter, "<span foreground='" + self.btnTMColor.get_color().to_string() + "'>" + info[1]  + "</span> ",-1)
                textIter = self.txtBuffer.get_end_iter()
                self.txtBuffer.insert_markup(textIter, "<span foreground='" + self.btnTextColor.get_color().to_string() + "'>" + " ".join(info[4:]) + "</span> " + "\n", -1)
                textIter = self.txtBuffer.get_end_iter()

    def setHolidayList(self):
        """[summary]
        gcalcliから取得した祝日をカレンダーに設定
        """
        if len(HOLIDAY_CALENDAR) == 0:
            return
        montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli " + "--calendar \"" + HOLIDAY_CALENDAR + "\" --nocolor agenda --tsv " + montStart.isoformat() + " " + montFinish.isoformat())
        for sch in schedules:
            if len(sch) > 0:
                info = sch.split("\t")
                day = datetime.strptime(info[0], "%Y-%m-%d")
                self.setHoliday(day.day, " ".join(info[4:]))

    def on_miExit_activate(self,widget):
        """[summary]
        終了メニューのイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        self._saveConf()
        Gtk.main_quit()

    def on_wCalendar_destroy(self,widget):
        """[summary]
        ウィンドウ破棄のイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        Gtk.main_quit()

    def on_miSetting_activate(self, widget):
        """[summary]
        設定ダイアログを開く
        Arguments:
            widget {[type]} -- [description]
        """
        global GCAL_PATH
        global EVENT_CALENDAR
        global HOLIDAY_CALENDAR
        self.btnFileChoose.set_current_folder(os.path.expanduser(GCAL_PATH))
        self.txtEventCalendar.set_text(EVENT_CALENDAR)
        self.txtHolidayCalendar.set_text(HOLIDAY_CALENDAR)
        self.sclOpecity.set_value(self.opacity * 100)
        self.settingDialog.show_all()

    def on_btnSettingOK_clicked(self, widget):
        """[summary]
        設定ダイアログのOKボタンイベント
        設定を保存してダイアログを閉じる
        Arguments:
            widget {[type]} -- [description]
        """
        global GCAL_PATH
        global EVENT_CALENDAR
        global HOLIDAY_CALENDAR
        GCAL_PATH = self.btnFileChoose.get_current_folder()
        EVENT_CALENDAR = self.txtEventCalendar.get_text()
        HOLIDAY_CALENDAR = self.txtHolidayCalendar.get_text()
        self.opacity = self.sclOpecity.get_value() / 100
        self._saveConf()
        self.setEventDayList()
        self.settingDialog.hide()
 
    def on_btnSettingCancel_clicked(self, widget):
        """[summary]
        設定ダイアログのキャンセルボタンイベント
        ダイアログを閉じる
        Arguments:
            widget {[type]} -- [description]
        """
        self.settingDialog.hide()

    def res_cmd(self, cmd):
        """[summary]
        cmdで指定されたコマンドをサブプロセスで実行し、結果をひとつの文字列で返却する
        Arguments:
            cmd {[type]} -- [description]
        
        Returns:
            [type] -- [description]
        """
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            shell=True).communicate()[0].decode("utf-8", "ignore")

    def res_cmd_lfeed(self, cmd):
        """[summary]
        cmdで指定されたコマンドをサブプロセスで実行し、結果をリストで返す（末尾改行）
        Arguments:
            cmd {[type]} -- [description]
        
        Returns:
            [type] -- [description]
        """
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            shell=True).stdout.readlines()

    def res_cmd_no_lfeed(self, cmd):
        """[summary]
        cmdで指定されたコマンドをサブプロセスで実行し、結果をリストで返す（末尾改行なし）
        Arguments:
            cmd {[type]} -- [description]
        
        Returns:
            [type] -- [description]
        """
        return [bytes(x).decode("utf-8", "ignore").rstrip("\n") for x in self.res_cmd_lfeed(cmd)]

    def set_style(self):
        """
        Change Gtk+ Style
        """
        provider = Gtk.CssProvider()
        # Demo CSS kindly provided by Numix project
        provider.load_from_path(join(WHERE_AM_I, 'gcalcal.css'))
        screen = Gdk.Display.get_default_screen(Gdk.Display.get_default())
        # I was unable to found instrospected version of this
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

if __name__ == '__main__':
    myCalendar()
    Gtk.main()
