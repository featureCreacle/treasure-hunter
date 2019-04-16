Xf = 9 #forest rows
Yf = 9 #forest columns

#from kivy.uix import *
from functools import partial
from forest_class import *
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle, Color

class icon_button(Button):
    def set_icons(self, icon, fit = False):
        with self.canvas:
            self.rect = Rectangle(source = icon)
        if fit:
            self.bind(pos=self.redraw_fit, size=self.redraw_fit)
        else:
            self.bind(pos=self.redraw, size=self.redraw)

    def change_icon(self, icon):
        if self.rect:
            self.rect.source = icon

    def redraw_fit(self, *args):
        size = (self.size[0], self.size[1]) if self.size[0] < self.size[1] else (self.size[1], self.size[0])
        self.rect.size = (size[0], size[0])
        sizediff = float((size[1] - size[0])) / 2
        pos = (self.pos[0], self.pos[1] + sizediff) if size[0] == self.size[0] else (
        self.pos[0] + sizediff, self.pos[1])
        self.rect.pos = pos

    def redraw(self, *args):
        self.rect.size = self.size
        self.rect.pos  = self.pos


class cell(icon_button):
    def __init__(self, **kwargs):
        super(cell,self).__init__(**kwargs)
        self.pressed = False
        self.tapTimer = None

    def set_tree_cordinate(self,x,y):
        self.tree_x = x
        self.tree_y = y
        self.treeCord = (x,y)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.pressed = True
            if touch.is_double_tap:
                Clock.unschedule(self.tapTimer)
                self.uncover_tree()
            else:
                self.create_longtap_clock(touch)
                self.create_tap_clock(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if not self.collide_point(*touch.pos):
                touch.ungrab(self)
        elif self.collide_point(*touch.pos):
            touch.grab(self)
            self.select_scan_area(touch, 1)

    def on_touch_up(self, touch):
        if  touch.grab_current is self:
            self.delete_longtap_clock(touch)
            self.pressed = False
            self.parent.forest_engine.restore_all_icons()
            isLongTap = (touch.time_end-touch.time_start)>0.5
            if isLongTap:
                self.check_near_tree()

    def check_near_tree(self):
        self.parent.forest_engine.check_near(self.tree_x, self.tree_y)

    def uncover_tree(self):
        self.parent.forest_engine.get_zakladka(self.tree_x, self.tree_y)

    def mark_tree(self, touch, time):
        if not self.pressed:
            self.parent.forest_engine.mark_tree_event(self.tree_x, self.tree_y)

    def select_scan_area(self, touch, time):
        self.parent.forest_engine.select_scan_area(self.tree_x, self.tree_y)

    def create_longtap_clock(self, touch):
        callback = partial(self.select_scan_area, touch)
        Clock.schedule_once(callback, 0.55)
        touch.ud['longtap'] = callback

    def delete_longtap_clock(self, touch):
        try:
            Clock.unschedule(touch.ud['longtap'])
        except KeyError:
            pass

    def create_tap_clock(self, touch):
        callback = partial(self.mark_tree, touch)
        Clock.schedule_once(callback, 0.26)
        self.tapTimer = callback

class forest_grid(GridLayout):
    def __init__(self, **kwargs):
        super(forest_grid, self).__init__(**kwargs)
        self.alertsCount = None
        self.root = None

    def plant_the_forest(self, N, M, treeIcon = icons[iconEnum['tree']]):
        self.clear_widgets(self.children)
        self.rows = N
        self.cols = M
        self.buttons = []
        treeButMap = []
        i = 0
        while (i < N):
            j = 0
            rowButtons = []
            while (j < M):
                but = cell()
                but.set_icons(treeIcon, True)
                # with but.canvas:
                #     but.rect = Rectangle(source=treeIcon, size=(32, 32))
                but.set_tree_cordinate(i,j)
                self.add_widget(but)
                rowButtons.append(but)
                j += 1
            treeButMap.append(rowButtons)
            i += 1
        self.treeButMap = treeButMap
        self.forest_engine = forest_abstract(master=self, N=N, M=M)
        self.update_alertsRemains()
        self.set_root(self.root)

    def set_root(self, root=None):
        if root != None:
            self.root = root
        else:
            root = self.parent
            while root != None:
                self.root = root
                root = self.root.parent

    def do_layout(self, *largs):
        super(forest_grid,self).do_layout(*largs)
        #self.update_buttons()

    def update_buttons(self, *args):
        i = 0
        while (i < self.rows):
            j = 0
            while (j < self.cols):
                but = self.treeButMap[i][j]
                but.rect.pos = (but.center_x - 16, but.center_y - 16)
                j += 1
            i += 1

    def set_icon_for_cell(self, x, y, icon):
        #self.treeButMap[x][y].rect.source = icon
        self.treeButMap[x][y].change_icon(icon)

    def update_alertsRemains(self):
        if self.alertsCount != None:
            self.alertsCount.text = str(self.forest_engine.alertsRemains)

    def new_forest(self, *args):
        self.root.clear_final_message()
        master = self
        N = self.rows
        M = self.cols
        self.forest_engine.set_defaults(master=master, N = N, M = M)
        self.forest_engine.restore_all_icons()
        self.update_alertsRemains()

    def hint(self, *args):
        self.forest_engine.hint()

    def show_final_message(self, result = gameResultEmum['confused']):
        self.root.show_final_message(result, self.new_forest)

    def show_settings(self, *args):

        self.root.show_settings_panel(func=self.apply_settings, forest_config = [self.rows, self.cols])

    def apply_settings(self, *args):
        self.root.clear_settings_panel()
        rows = int(args[0])
        cols = int(args[1])
        if rows != self.rows or cols != self.cols:
            self.plant_the_forest(rows, cols)

class root_layout(FloatLayout):
    def __init__(self, *kwargs):
        super(root_layout,self).__init__(*kwargs)
        self.msg_childrens = []
        self.stng_childrens = []

    def redrawMsg(self, *args):
        shift = 0.10
        self.msg_rect.size = (self.msgLayout.size[0]*(1+shift*2),
                              self.msgLayout.size[1]*(1+shift*2))
        self.msg_rect.pos  = (self.msgLayout.pos[0]-self.msgLayout.size[0]*shift,
                              self.msgLayout.pos[1]-self.msgLayout.size[0]*shift)
        # self.msg_rect.size = self.msgLayout.size
        # self.msg_rect.pos = self.msgLayout.pos

    def redrawStng(self, *args):
        self.stng_rect.pos = self.stngLayout.pos
        self.stng_rect.size = self.stngLayout.size

    def show_final_message(self, result = gameResultEmum['confused'], func = None):
        self.msgLayout = BoxLayout(size_hint=(0.5,0.5),
                                   pos_hint = {'center_x': 0.5, 'center_y': 0.55 },
                                   orientation = 'vertical')

        text, color = ('You WIN!', [0.1,0.1,0.7,1]) if result == gameResultEmum['win'] \
            else ('You LOSE!',[0.9,0.2,0.2,1]) if result == gameResultEmum['lose'] \
            else ('Im so confused', [0.8,0.8,0.5,1])
        text_button = 'Halp!1' if result == gameResultEmum['confused'] else 'New Game'

        self.msgLable = Label(bold=True, color = color, font_size = '70sp', text = text)
        self.msgButton = Button(text = text_button, bold=True, color = color, font_size = '50sp')

        if func != None:
            self.msgButton.bind(on_press=func)

        self.msgLayout.add_widget(self.msgLable)
        self.msgLayout.add_widget(self.msgButton)
        self.add_widget(self.msgLayout)
        with self.msgLayout.canvas.before:
            Color(0.5, 0.5, 0.5, 0.8)
            self.msg_rect = Rectangle(pos_hint={'center_x': 0.5, 'center_y': 0.5 }, size_hint=(0.3,0.3))
        self.msgLayout.bind(pos=self.redrawMsg, size=self.redrawMsg)
        self.msg_childrens.extend([self.msgLable, self.msgButton, self.msgLayout])

    def clear_final_message(self, *args):
        self.clear_widgets(self.msg_childrens)
        self.msg_childrens = []

    def show_settings_panel(self, func=None, forest_config = []):
        self.stngLayout = BoxLayout(size_hint=(0.3, 0.4),
                                   pos_hint={'center_x': 0.5, 'center_y': 0.75},
                                   orientation='vertical')
        self.stngLayout_up = BoxLayout(size_hint=(1, 0.6),
                                       pos_hint={'center_x': 0.5, 'center_y': 0.8},
                                       spacing = 5, padding = 10) #orientation='vertical',
        self.stngLayout_bottom = BoxLayout(size_hint=(1, 0.4),
                                   pos_hint={'center_x': 0.5, 'center_y': 0.3}, spacing = 40, padding = 10)
        color = [0.1, 0.3, 0.1, 1]
        self.stng_rows = TextInput(text=str(forest_config[0]),multiline=False, font_size = '40sp',size_hint=(0.3, 0.8))
                                   #,size_hint=(0.3, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.stng_cols = TextInput(text=str(forest_config[1]),multiline=False, font_size='40sp',size_hint=(0.3, 0.8))
                                   #,size_hint=(0.3, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.stng_label_x = Label(text= 'X', bold=True, color = color, font_size = '50sp',size_hint=(0.3, 0.8))
        self.stngLayout_up.add_widget(self.stng_rows)
        self.stngLayout_up.add_widget(self.stng_label_x)
        self.stngLayout_up.add_widget(self.stng_cols)
        self.stng_ok_button = icon_button()
        self.stng_ok_button.set_icons(icons[iconEnum['ok']], True)
        self.stng_no_button = icon_button()
        self.stng_no_button.set_icons(icons[iconEnum['no']], True)
        self.stngLayout_bottom.add_widget(self.stng_no_button)
        self.stngLayout_bottom.add_widget(self.stng_ok_button)
        self.stngLayout.add_widget(self.stngLayout_up)
        self.stngLayout.add_widget(self.stngLayout_bottom)
        self.add_widget(self.stngLayout)
        with self.stngLayout.canvas.before:
            Color(0.5, 0.5, 0.5, 1)
            self.stng_rect = Rectangle(pos_hint={'center_x': 0.5, 'center_y': 0.55 }, size_hint=(0.5,0.8))
        self.stngLayout.bind(pos=self.redrawStng, size=self.redrawStng)
        self.stng_ok_button.bind(on_press= lambda *args: func(self.stng_rows.text, self.stng_cols.text))
        self.stng_no_button.bind(on_press=self.clear_settings_panel)
        self.stng_childrens.extend([self.stngLayout, self.stngLayout_up, self.stngLayout_bottom, self.stng_label_x,
                                    self.stng_rows, self.stng_cols, self.stng_ok_button, self.stng_no_button])

    def clear_settings_panel(self, *args):
        self.clear_widgets(self.stng_childrens)
        self.stng_childrens = []

class main(App):
    def __init__(self, **kwargs):
        super(main, self).__init__(**kwargs)
        self.title = 'Treasure hunter Jr'
        self.icon = 'res/32/sweet.gif'
        self.root = root_layout()
        self.screenPanel = BoxLayout(spacing = 5)
        self.screenPanel.orientation = 'vertical'
        self.forest_widget = forest_grid()
        self.bottom_panel = BoxLayout(spacing = 5, size_hint = (1,0.1))
        self.forest_widget.alertsCount = Label(bold=True, color = [1,0.1,0.1,0.8], font_size = '32sp', text='-')
        self.hint_button = Button(bold=True, color = [0.0,0.5,0.6,0.8], font_size = '32sp', text= 'Hint')
        self.goBaka_button = Button(bold=True, color = [0.0,0.5,0.8,0.8], font_size = '32sp', text= 'Go Baka Go')
        self.settings_button = icon_button(size_hint = (0.25,1))
        self.settings_button.set_icons(icons[iconEnum['settings']])
        self.bottom_panel.add_widget(self.forest_widget.alertsCount)
        self.bottom_panel.add_widget(self.hint_button)
        self.bottom_panel.add_widget(self.goBaka_button)
        self.bottom_panel.add_widget(self.settings_button)
        self.screenPanel.add_widget(self.forest_widget)
        self.screenPanel.add_widget(self.bottom_panel)
        self.root.add_widget(self.screenPanel)
        self.forest_widget.plant_the_forest(N=Xf, M=Yf, treeIcon=icons[iconEnum['tree']])
        self.hint_button.bind(on_press=self.forest_widget.hint)
        self.goBaka_button.bind(on_press=self.goBakaGoThread)
        self.settings_button.bind(on_press=self.forest_widget.show_settings)

    def build(self):
        return self.root

    def goBakaGoThread(self, *args):
        engine = self.forest_widget.forest_engine
        if engine.stepStat != AIStatEnum['inProgress'] and \
            engine.stepStat != AIStatEnum['cantDone'] and not engine.gameIsOver:
                engine.doStep()
                self.forest_widget.update_alertsRemains()
                if engine.stepStat == AIStatEnum['done'] and not engine.gameIsOver:
                    Clock.schedule_once(self.goBakaGoThread, 0.1)
                else:
                    self.stopBaka()
        elif engine.gameIsOver or engine.stepStat == AIStatEnum['cantDone']:
            self.stopBaka()

    def goBakaGo(self, *args):
        Clock.schedule_once(self.goBakaGoThread)

    def stopBaka(self):
        Clock.unschedule(self.goBakaGoThread)
        engine = self.forest_widget.forest_engine
        if engine.Result == gameResultEmum['confused']:
            self.root.show_final_message(engine.Result, self.root.clear_final_message)

if __name__ == '__main__':
    main().run()