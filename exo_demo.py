from psychopy import core, event, visual
import numpy as np
import yaml
from ExoDisplay import ExoDisplay

class ExoDemoGame:

    def __init__(self, config='default'):
        # load config
        self.config = yaml.load(open('config/'+config+'.yml'),Loader=yaml.FullLoader)

        # load hand/finger params
        self.num_hands = self.config['num_hands']
        self.fingers_per_hand = self.config['fingers_per_hand']
        self.num_fingers = self.num_hands * self.fingers_per_hand 

        # set display 
        self.win = visual.Window(size=(self.config['screen_width'], self.config['screen_height']),
                                 color=self.config['bg_color'], units='height')
        self.exo_display = ExoDisplay(self.win, config=config)

        # add key controls
        # event.globalKeys.add(key='q', modifiers=['ctrl'], func=self.quit)
        # event.globalKeys.add(key='o', func=self.exo_display.key_stims[0].setBaseColor, func_kwargs=dict(color=[-0.5,-0.5,-0.5]))
        event.globalKeys.add(key='s', modifiers=['ctrl'], func=self.toggle_exp)

        if not(self.exo_display.exo_active):
            from psychopy.iohub.client import launchHubServer
            self.io = launchHubServer()
            self.kb = self.io.devices.keyboard
            self.key_codes = ['a','w','e','r','b']

        # rough SRT demo
        self.exp_running = False
        self.trial_clock = core.Clock()
        self.trial_time = 1.0 # seconds
        self.target_time = 0.5 # seconds
        self.target_finger = 0
        self.finger_pressed = False

    def toggle_exp(self):
        self.exp_running = not(self.exp_running)
        self.reset_trial()

    def reset_trial(self):
        self.trial_clock.reset()
        last_target = self.target_finger
        while self.target_finger == last_target:
            self.target_finger = np.random.randint(0,5)
        self.finger_pressed = False
        for key in self.exo_display.key_stims:
            key.setBaseColor(self.exo_display.key_color)
        self.exo_display.key_stims[self.target_finger].setBaseColor(self.exo_display.cue_color)

    def run_trial(self):
        if any(self.exo_display.keydowns) and not(self.finger_pressed):
            self.finger_pressed = True
            pressed_key = np.where(self.exo_display.keydowns==True)[0][0]
            if pressed_key != self.target_finger:
                self.exo_display.key_stims[self.target_finger].setBaseColor(self.exo_display.fail_color)
            elif (pressed_key == self.target_finger) and (self.trial_clock.getTime() <= self.target_time):
                self.exo_display.key_stims[self.target_finger].setBaseColor(self.exo_display.success_color)
            else:
                self.exo_display.key_stims[self.target_finger].setBaseColor(self.exo_display.slow_color)
        if self.trial_clock.getTime() > self.trial_time:
            self.reset_trial()

    def check_keys(self):
        events = self.kb.getKeys()
        for kbe in events:
            if kbe.key in self.key_codes:
                if kbe.type == 'KEYBOARD_PRESS':
                    self.exo_display.spoof_keydowns[int(np.where(kbe.key==np.array(self.key_codes))[0])]=True
                elif kbe.type == 'KEYBOARD_RELEASE':
                    self.exo_display.spoof_keydowns[int(np.where(kbe.key==np.array(self.key_codes))[0])]=False
            elif (kbe.key == 'q') and (len(kbe.modifiers)==1):
                if kbe.modifiers[0]=='lctrl': self.quit()

    def run_main_loop(self):
        while True:
            if not(self.exo_display.exo_active):
                self.check_keys()
            self.exo_display.update_inputs()
            if self.exp_running:
                self.run_trial()
            self.exo_display.draw()
            self.win.flip()

    def quit(self):
        if self.exo_display.exo_active:
            self.exo_display.exo.stop()
        core.quit()

if __name__ == '__main__':
    game = ExoDemoGame()
    game.run_main_loop()
