import os, sys, yaml, argparse
import numpy as np
from psychopy import core, event, visual
from ExoDisplay import ExoDisplay

# interpret command line arguments
parser = argparse.ArgumentParser(description='Sequence learning experiment parameters')
parser.add_argument('-s','--subjectid', help='Subject ID',default='demo')
parser.add_argument('-c','--config', help='Configuration file',default='demo')
parser.add_argument('-fs','--fullscreen', help='Fullscreen mode', action='store_true', default=False)
args = parser.parse_args()

class SequenceGame:

    def __init__(self):
        # load command line args
        self.args = args

        # load config
        try:
            with open(os.path.join('config',self.args.config+'.yml')) as f:
                self.config = yaml.load(f, Loader=yaml.FullLoader)
        except:
            print('Configuration file '+self.args.config+'.yml not found')
            sys.exit(1)

        # set display 
        self.win = visual.Window(size=(self.config['screen_width'], self.config['screen_height']),
                                 color=self.config['bg_color'], units='height',
                                 fullscr=self.args.fullscreen)
        self.exo_display = ExoDisplay(self.win, config=self.config)

        # file recording
        self.finger_round = self.config['finger_round']
        self.time_round = self.config['time_round']
        self.subject_path = os.path.join('logs',self.args.subjectid)
        if self.args.subjectid != 'demo':
            if os.path.exists(self.subject_path):
                raise RuntimeError('subject path already exists!')
        if not(os.path.exists(self.subject_path)): os.mkdir(self.subject_path)

        # add key controls
        event.globalKeys.add(key='q', modifiers=['ctrl'], func=self.quit)

        if not(self.exo_display.exo_active):
            from psychopy.iohub.client import launchHubServer
            self.io = launchHubServer()
            self.kb = self.io.devices.keyboard
            self.key_codes = ['q','w','e','r','v','n','u','i','o','p']

        self.run_msg_text = 'Run {} of {}'
        self.exp_end_text = 'All done!'
        self.run_msg = visual.TextStim(win=self.win,
            text='', pos=(0,-0.2),
            color=self.exo_display.cue_color,
            height=0.08)
        self.score_msg_text = 'Total score: {}'
        self.score_msg = visual.TextStim(win=self.win,
            text='', pos=(0,-0.3),
            color=self.exo_display.success_color,
            height=0.08)

        # sequence learning variables
        self.trial_clock = core.Clock()
        self.start_clock = core.Clock()
        self.start_hand = self.config['start_hand']
        self.trial_stage = 'cue' # ['cue', 'press', 'feedback']
        self.seq_in_trial = 0
        self.START_WAIT_TIME = self.config['start_wait_time']
        self.SEQ_PER_TRIAL = self.config['seq_per_trial']
        self.CUE_TIME = self.config['cue_time']
        self.FEEDBACK_TIME = self.config['feedback_time']
        self.ITI_TIME = self.config['iti_time']
        self.NUM_RUNS = self.config['num_runs']
        self.TRIALS_PER_RUN = self.config['trials_per_run']
        self.SEQUENCES = self.config['sequences']
        self.trial_num = 0
        self.run_num = 0
        self.score = 0
        self.trial_base_order = self.config['sequence_order']
        self.trial_order = np.tile(self.trial_base_order,
            int(self.TRIALS_PER_RUN/len(self.trial_base_order)))
        self.seq_times = {}
        for k in self.SEQUENCES.keys():
            self.seq_times[k] = np.array([])
        self.set_sequence()
        self.write_frame_header()
        self.write_trial_header() 
        self.reset_for_start()

    def set_sequence(self):
        self.next_seq_id = self.trial_order[self.trial_num]
        self.next_seq = self.SEQUENCES[self.next_seq_id]
        self.exo_display.cue_display.active_hand = self.next_seq['hand']
        self.sequence = np.array(self.next_seq['seq'])

    def reset_for_start(self):
        self.exp_stage = 'wait'
        if self.run_num > 0:
            self.score_msg.text = self.score_msg_text.format(self.score)
        if self.run_num < self.NUM_RUNS:
            self.run_msg.text = self.run_msg_text.format(self.run_num+1,self.NUM_RUNS)
        else:
            self.run_msg.text = self.exp_end_text
        self.exo_display.cue_display.set_for_start(self.start_hand)
        for key in self.exo_display.key_stims:
            key.setBaseColor(self.exo_display.cue_color)
        self.start_keys_pressed = np.full(self.exo_display.num_fingers, False)
        self.start_initiated = False

    def wait_for_start(self):
        self.run_msg.draw()
        self.score_msg.draw()
        for pressed_key in np.where(self.exo_display.keydowns==True)[0]:
            self.start_keys_pressed[pressed_key] = True
            self.exo_display.key_stims[pressed_key].setBaseColor(self.exo_display.success_color)

        if ((sum(self.start_keys_pressed)>=self.exo_display.num_active_fingers)
                and not(self.start_initiated)):
            self.start_initiated = True
            self.start_clock.reset()

        if self.start_initiated and self.start_clock.getTime()>self.START_WAIT_TIME:
            if self.run_num < self.NUM_RUNS:
                self.reset_for_exp()
            else:
                self.quit()

    def reset_for_exp(self):
        self.exp_stage = 'run'
        self.reset_for_trial()

    def reset_for_trial(self):
        self.set_sequence()
        self.seq_in_trial = 0
        self.trial_stage = 'cue'
        self.trial_clock.reset()
        self.reset_for_seq()

    def reset_for_seq(self):
        for key in self.exo_display.key_stims:
            key.setBaseColor(self.exo_display.key_color)
        self.key_num_to_press = 0
        self.key_to_press = self.sequence[0]
        self.correct_in_seq = np.full(len(self.sequence),False)
        self.seq_timings = np.full(len(self.sequence),0.0)

    def reset_new_keydowns(self):
        self.exo_display.new_keydowns[:] = False

    def write_frame_header(self):
        self.frame_file = open(self.subject_path+'/frame.csv','w')
        self.frame_file.write('trial_time,')
        for finger in range(self.config['num_fingers']):
            self.frame_file.write('f_'+str(finger)+',')
        self.frame_file.write('hand,')
        self.frame_file.write('seq_id,')
        self.frame_file.write('trial,')
        self.frame_file.write('run\n')

    def write_frame(self):
        self.frame_file.write(
            str(np.round(self.trial_clock.getTime(),self.time_round))
                +',')
        for finger in range(self.config['num_fingers']):
            self.frame_file.write(
                str(np.round(self.exo_display.angle_filt[finger],self.finger_round))
                +',')
        self.frame_file.write(self.next_seq['hand']+',')
        self.frame_file.write(self.next_seq_id+',')
        sequence_execution_num = (self.seq_in_trial   
            +self.trial_num*self.SEQ_PER_TRIAL
            +self.run_num*(self.SEQ_PER_TRIAL*self.TRIALS_PER_RUN))
        self.frame_file.write(str(sequence_execution_num)+',')
        self.frame_file.write(str(self.run_num)+'\n')

    def write_trial_header(self):
        self.trial_file = open(self.subject_path+'/trial.csv','w')
        self.trial_file.write('move_time,')
        for press in range(len(self.sequence)):
            self.trial_file.write('p_'+str(press)+',')
        self.trial_file.write('score,')
        self.trial_file.write('hand,')
        self.trial_file.write('seq_id,')
        self.trial_file.write('trial,')
        self.trial_file.write('run\n')

    def write_trial(self):
        self.trial_file.write(str(np.round(self.seq_time,self.time_round))+',')
        for press in range(len(self.sequence)):
            self.trial_file.write(str(np.round(self.seq_timings[press],self.time_round))
                +',')
        self.trial_file.write(str(self.add_score)+',')
        self.trial_file.write(self.next_seq['hand']+',')
        self.trial_file.write(self.next_seq_id+',')
        sequence_execution_num = (self.seq_in_trial   
            +self.trial_num*self.SEQ_PER_TRIAL
            +self.run_num*(self.SEQ_PER_TRIAL*self.TRIALS_PER_RUN))
        self.trial_file.write(str(sequence_execution_num)+',')
        self.trial_file.write(str(self.run_num)+'\n')

    def run_trial(self):
        self.exo_display.cue_display.draw()
        if self.trial_stage == 'cue':
            self.exo_display.cue_display.set_cue(
                seq=str(self.sequence+1)[1:-1])
            if self.trial_clock.getTime() > self.CUE_TIME:
                self.trial_stage = 'press'
                self.exo_display.cue_display.set_all_idle()
                self.reset_new_keydowns()
                self.trial_clock.reset()
        elif self.trial_stage == 'press':
            self.write_frame()
            self.key_to_press = self.sequence[self.key_num_to_press]
            self.exo_display.key_stims[self.key_to_press].setBaseColor(self.exo_display.cue_color)
            if any(self.exo_display.new_keydowns):
                pressed_key = np.where(self.exo_display.new_keydowns==True)[0][0]
                if pressed_key == self.key_to_press:
                    self.correct_in_seq[self.key_num_to_press] = True
                    self.exo_display.key_stims[self.key_to_press].setBaseColor(self.exo_display.success_color)
                else:
                    self.correct_in_seq[self.key_num_to_press] = False
                    self.exo_display.key_stims[self.key_to_press].setBaseColor(self.exo_display.fail_color)
                self.seq_timings[self.key_num_to_press] = self.trial_clock.getTime()
                self.key_num_to_press += 1
                self.exo_display.new_keydowns[:] = False
                if self.key_num_to_press >= len(self.sequence):
                    self.trial_stage = 'feedback'
                    self.seq_time = self.seq_timings[-1]-self.seq_timings[0]
                    if all(self.correct_in_seq):
                        self.seq_correct = True
                        self.seq_times[self.next_seq_id] = np.append(self.seq_times[self.next_seq_id],self.seq_time)
                        if self.seq_time < np.median(self.seq_times[self.next_seq_id]):
                            self.exo_display.cue_display.set_feedback('fast')
                            self.add_score = 3
                        else:
                            self.exo_display.cue_display.set_feedback('success')
                            self.add_score = 1
                    else:
                        self.seq_correct = False
                        self.exo_display.cue_display.set_feedback('fail')
                        self.add_score = 0
                    self.score += self.add_score
                    self.write_trial()
                    self.trial_clock.reset()
                    self.seq_in_trial+=1
        elif self.trial_stage == 'feedback':
            if self.trial_clock.getTime() > self.FEEDBACK_TIME:
                self.exo_display.cue_display.set_all_idle()
                if self.seq_in_trial < self.SEQ_PER_TRIAL:
                    self.reset_for_seq()
                    self.trial_clock.reset()
                    self.trial_stage = 'press'
                    self.reset_new_keydowns()
                else:
                    self.trial_stage = 'iti'
                    self.trial_clock.reset()
                    self.reset_for_seq()
        elif self.trial_stage == 'iti':
            if self.trial_clock.getTime() > self.ITI_TIME:
                self.trial_num += 1
                if self.trial_num >= self.TRIALS_PER_RUN:
                    self.trial_num = 0
                    self.run_num += 1
                    self.reset_for_start()
                else:
                    self.reset_for_trial()

    def check_keys(self):
        events = self.kb.getKeys()
        for kbe in events:
            if kbe.key in self.key_codes:
                if kbe.type == 'KEYBOARD_PRESS':
                    self.exo_display.spoof_keydowns[int(np.where(kbe.key==np.array(self.key_codes))[0])]=True
                elif kbe.type == 'KEYBOARD_RELEASE':
                    self.exo_display.spoof_keydowns[int(np.where(kbe.key==np.array(self.key_codes))[0])]=False

    def run_main_loop(self):
        while True:
            if not(self.exo_display.exo_active):
                self.check_keys()
            self.exo_display.update_inputs()
            if self.exp_stage == 'wait':
                self.wait_for_start()
            elif self.exp_stage == 'run':
                self.run_trial()
            self.exo_display.draw()
            self.win.flip()

    def quit(self):
        self.frame_file.close()
        self.trial_file.close()
        if self.exo_display.exo_active:
            self.exo_display.exo.stop()
        core.quit()

if __name__ == '__main__':
    game = SequenceGame()
    game.run_main_loop()
