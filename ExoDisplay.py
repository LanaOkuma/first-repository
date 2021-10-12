from psychopy import visual, core
import numpy as np
import yaml, math

def gen_key_shape(win, width=0.1, height=0.05,
        corner_rad=0.02, line_width=2.5, corner_pts=5,
        fill_color=[-0.5,-0.5,-0.5], line_color=[0.1,0.1,0.1],
        xpos=0, ypos=0):
    num_circ_points = 4*corner_pts+5
    circ_points = np.linspace(0,2*np.pi,num=num_circ_points)
    cxs = corner_rad*np.cos(circ_points)
    cys = corner_rad*np.sin(circ_points)
    qts = corner_pts+2
    xs = np.zeros(num_circ_points+3)
    xs[0:qts] = cxs[0:qts]+0.5*width
    xs[qts:2*qts] = cxs[qts-1:2*qts-1]-0.5*width
    xs[2*qts:3*qts] = cxs[2*qts-2:3*qts-2]-0.5*width
    xs[3*qts:4*qts] = cxs[3*qts-3:4*qts-3]+0.5*width
    ys = np.zeros(num_circ_points+3)
    ys[0:qts] = cys[0:qts]+0.5*height
    ys[qts:2*qts] = cys[qts-1:2*qts-1]+0.5*height
    ys[2*qts:3*qts] = cys[2*qts-2:3*qts-2]-0.5*height
    ys[3*qts:4*qts] = cys[3*qts-3:4*qts-3]-0.5*height
    vertices = np.vstack([xs,ys]).T
    shape = visual.ShapeStim(win,
        vertices=vertices,
        lineWidth=line_width,
        lineColor=line_color,
        fillColor=fill_color,
        pos=(xpos,ypos), interpolate=True)
    return shape

class KeyDisplay:
    def __init__(self, key_width, key_height,
            base_expand, base_height,
            corner_rad, line_width, corner_pts,
            color, shadow_adjust_color, line_color, line_adjust_color,
            xpos, ypos, win):
        self.shadow_adjust_color = np.array(shadow_adjust_color)
        self.line_adjust_color = np.array(line_adjust_color)
        self.key_top = gen_key_shape(win, width=key_width, height=key_height,
            corner_rad=corner_rad, line_width=line_width, corner_pts=corner_pts,
            fill_color=color, line_color=line_color,
            xpos=xpos, ypos=ypos)
        self.key_bottom = gen_key_shape(win, width=key_width, height=key_height,
            corner_rad=corner_rad, line_width=line_width, corner_pts=corner_pts,
            fill_color=np.array(color)+self.shadow_adjust_color, line_color=line_color,
            xpos=xpos, ypos=ypos)
        self.base_top = gen_key_shape(win, width=key_width+base_expand, height=key_height+base_expand,
            corner_rad=corner_rad+base_expand, line_width=line_width, corner_pts=corner_pts,
            fill_color=color, line_color=line_color,
            xpos=xpos, ypos=ypos)
        self.base_bottom = gen_key_shape(win, width=key_width+base_expand, height=key_height+base_expand,
            corner_rad=corner_rad+base_expand, line_width=line_width, corner_pts=corner_pts,
            fill_color=np.array(color)+self.shadow_adjust_color, line_color=line_color,
            xpos=xpos, ypos=ypos-base_height)

    def setKeyColor(self, color):
        self.key_top.fillColor = np.array(color)
        self.key_bottom.fillColor = np.array(color)+self.shadow_adjust_color

    def setBaseColor(self, color):
        self.base_top.fillColor = np.array(color)
        self.base_bottom.fillColor = np.array(color)+self.shadow_adjust_color
        self.base_top.lineColor = np.array(color)+self.line_adjust_color
        self.base_bottom.lineColor = np.array(color)+self.line_adjust_color

    def setPos(self, ypos):
        self.key_top.pos = [self.key_top.pos[0], ypos]

    def draw(self):
        self.base_bottom.draw()
        self.base_top.draw()
        self.key_bottom.draw()
        self.key_top.draw()


class CueDisplay:

    def __init__(self, win, bg_color, cue_color, idle_color,
                 success_color, fail_color):
        # graphics
        self.bg_color = bg_color
        self.cue_color = cue_color
        self.idle_color = idle_color
        self.success_color = success_color
        self.fail_color = fail_color
        self.left_hand_light = visual.ImageStim(win,'hand-light.png',
            size=(0.15,0.15),pos=(-0.3,0.25), interpolate=True)
        self.left_hand_dark = visual.ImageStim(win,'hand-dark.png',
            size=(0.15,0.15),pos=(-0.3,0.25), interpolate=False)
        self.right_hand_light = visual.ImageStim(win,'hand-light.png',
            size=(0.15,0.15),pos=(0.3,0.25), interpolate=True, flipHoriz=True)
        self.right_hand_dark = visual.ImageStim(win,'hand-dark.png',
            size=(0.15,0.15),pos=(0.3,0.25), interpolate=False, flipHoriz=True)
        self.cue_outline = gen_key_shape(win, width=0.3, height=0.03,
        corner_rad=0.04, line_width=5, corner_pts=5,
        fill_color=self.bg_color, line_color=self.cue_color,
        xpos=0, ypos=0.25)
        self.cue_msg = visual.TextStim(win=win,
            text='', pos=(0,0.25),
            color=self.cue_color,
            height=0.08)

        self.feedback_msgs = {'fast':'+3',
                              'success':'+1',
                              'fail':'+0'}

        # logic
        self.active_hand = 'left' # 'left' or 'right'

        # reset to start
        self.set_all_idle()

    def draw(self):
        if self.active_hand == 'left':
            self.left_hand_light.draw()
            self.right_hand_dark.draw()
        elif self.active_hand == 'right':
            self.left_hand_dark.draw()
            self.right_hand_light.draw()
        else:
            self.left_hand_dark.draw()
            self.right_hand_dark.draw()
        self.cue_outline.draw()
        self.cue_msg.draw()

    def set_for_start(self, hand='left'):
        self.cue_outline.lineColor = self.idle_color
        self.cue_msg.text = 'Press All'
        self.cue_msg.color = self.cue_color
        self.active_hand = hand

    def set_all_idle(self):
        self.cue_outline.lineColor = self.idle_color
        self.cue_msg.text = ''

    def set_cue(self, seq='5 2 3 1 4'):
        self.cue_outline.lineColor = self.cue_color
        self.cue_msg.color = self.cue_color
        self.cue_msg.text = seq

    def set_feedback(self, feedback):
        self.cue_msg.text = self.feedback_msgs[feedback]
        if feedback == 'fast' or feedback == 'success':
            self.cue_msg.color = self.success_color
            self.cue_outline.lineColor = self.success_color
        elif feedback == 'fail':
            self.cue_msg.color = self.fail_color
            self.cue_outline.lineColor = self.fail_color

class ExoDisplay:

    def __init__(self, win, config):

        # load config
        self.config = config

        # load and start exo recording
        if self.config['use_exo']:
            self.exo_active = True
            from exoskeleton import Exoskeleton
            self.exo = Exoskeleton('output/passive', self.config['port'], 921600)
            self.exo.read(duration=10000, log=False, display=False)
        else:
            self.exo_active = False

        # load hand/finger params
        self.num_fingers = self.config['num_fingers']
        self.num_active_fingers = self.config['num_active_fingers']

        # load display params
        self.key_width = self.config['key_width']
        self.key_height = self.config['key_height']
        self.key_line_width = self.config['key_line_width']
        self.key_base_expand = self.config['key_base_expand']
        self.key_corner_rad = self.config['key_corner_rad']
        self.key_corner_pts = self.config['key_corner_pts']
        self.key_base_height = self.config['key_base_height']
        self.key_spacing = self.config['key_spacing']
        self.ypos_min = self.config['key_ypos_min']
        self.ypos_max = self.config['key_ypos_max']
        self.base_ypos = self.config['key_base_ypos']
        self.display_angle_min = self.config['display_angle_min']
        self.display_angle_max = self.config['display_angle_max']
        self.valid_angle_min = self.config['valid_angle_min']
        self.valid_angle_max = self.config['valid_angle_max']

        # set display
        self.key_color = self.config['key_color']
        self.key_line_color = self.config['key_line_color']
        self.shadow_adjust_color = self.config['shadow_adjust_color']
        self.line_adjust_color = self.config['line_adjust_color']
        self.success_color = self.config['success_color']
        self.slow_color = self.config['slow_color']
        self.fail_color = self.config['fail_color']
        self.cue_color = self.config['cue_color']
        self.xpos = np.arange(self.num_active_fingers)-(self.num_active_fingers-1)/2
        self.xpos = self.key_spacing*self.xpos
        self.key_stims = [KeyDisplay(
            key_width=self.key_width, key_height=self.key_height,
            base_expand=self.key_base_expand, base_height=self.key_base_height,
            corner_rad=self.key_corner_rad, line_width=self.key_line_width,
            corner_pts=self.key_corner_pts, color=self.key_color,
            shadow_adjust_color=self.shadow_adjust_color,
            line_color=self.key_line_color,
            line_adjust_color=self.line_adjust_color,
            xpos=self.xpos[finger], ypos=self.base_ypos, win=win)
                for finger in range(self.num_active_fingers)]
        self.cue_display = CueDisplay(win,
            bg_color=self.config['bg_color'],cue_color=self.cue_color,
            idle_color=self.key_color, success_color=self.success_color,
            fail_color=self.fail_color)

        # data input and filtering
        self.exo_clock = core.Clock()
        self.last_time = self.exo_clock.getTime()
        self.time_passed = 0
        self.filter_bool = self.config['use_filter']
        self.angle_raw = np.zeros(self.num_fingers)
        self.angle_filt = np.zeros(self.num_fingers)
        self.spoof_keydowns = np.full(self.num_fingers, False)
        self.keydowns = np.full(self.num_fingers, False)
        self.new_keydowns = np.full(self.num_fingers, False)
        filter_config = {
            'freq': 120, # Hz, dummy value, will be updated with time_passed
            'mincutoff': self.config['filter_fc_min'], # Hz, minimum cutoff frequency
            'beta': self.config['filter_beta'], # arbitrary units, speed coefficient
            'dcutoff': self.config['filter_d_cutoff'] # Hz, derivative cutoff frequency
            }
        self.filters = [OneEuroFilter(**filter_config) for filt in range(self.num_fingers)]

    def toggle_filter(self):
        self.filter_bool = not(self.filter_bool)

    def update_inputs(self):
        new_time = self.exo_clock.getTime()
        self.time_passed = new_time-self.last_time
        self.last_time = new_time

        # update inputs (all fingers)
        for finger in range(self.num_fingers):
            if self.exo_active:
                input_raw = exo.position[finger]
            else:
                if self.spoof_keydowns[finger]:
                    input_raw = 1.1*self.display_angle_max
                else:
                    input_raw = self.display_angle_min

            if (input_raw >= self.valid_angle_min) and (input_raw <= self.valid_angle_max):
                self.angle_raw[finger] = input_raw
            else:
                pass # ignore input if out of valid range, using previous value by default

            # # apply filtering
            if self.filter_bool:
                self.angle_filt[finger] = self.filters[finger](self.angle_raw[finger], self.time_passed)
            else:
                self.angle_filt[finger] = self.angle_raw[finger]

        # update stims
        for finger in range(self.num_active_fingers):
            if self.cue_display.active_hand == 'left':
                physical_finger = finger
            elif self.cue_display.active_hand == 'right':
                physical_finger = finger+self.num_active_fingers
            self.key_stims[finger].setPos(
                self.ypos_min+(self.ypos_max-self.ypos_min)
                *np.clip(self.display_angle_min,
                         self.angle_filt[physical_finger],
                         self.display_angle_max)
                 /(self.display_angle_max-self.display_angle_min))

            if self.angle_filt[physical_finger] >= self.display_angle_max:
                if not(self.keydowns[finger]):
                    self.new_keydowns[finger] = True
                self.keydowns[finger] = True
            elif self.angle_filt[physical_finger] < self.display_angle_max:
                self.keydowns[finger] = False

    def draw(self):
        for stim in self.key_stims: stim.draw()
        self.cue_display.draw()

# ----------------------------------------------------------------------------

class OneEuroFilter(object):

    def __init__(self, freq, mincutoff=1.0, beta=0.0, dcutoff=1.0):
        if freq<=0:
            raise ValueError("freq should be >0")
        if mincutoff<=0:
            raise ValueError("mincutoff should be >0")
        if dcutoff<=0:
            raise ValueError("dcutoff should be >0")
        self.__freq = float(freq)
        self.__mincutoff = float(mincutoff)
        self.__beta = float(beta)
        self.__dcutoff = float(dcutoff)
        self.__x = LowPassFilter(self.__alpha(self.__mincutoff))
        self.__dx = LowPassFilter(self.__alpha(self.__dcutoff))
        self.__lasttime = None
        
    def __alpha(self, cutoff):
        te    = 1.0 / self.__freq
        tau   = 1.0 / (2*math.pi*cutoff)
        return  1.0 / (1.0 + tau/te)

    def __call__(self, x, time_passed=None):
        # ---- update the sampling frequency based on timestamps
        if time_passed:
            self.__freq = 1.0 / float(time_passed)
        # ---- estimate the current variation per second
        prev_x = self.__x.lastValue()
        dx = 0.0 if prev_x is None else (x-prev_x)*self.__freq
        edx = self.__dx(dx, None, alpha=self.__alpha(self.__dcutoff))
        # ---- use it to update the cutoff frequency
        cutoff = self.__mincutoff + self.__beta*math.fabs(edx)
        # ---- filter the given value
        return self.__x(x, None, alpha=self.__alpha(cutoff))

# ----------------------------------------------------------------------------

class LowPassFilter(object):

    def __init__(self, alpha):
        self.__setAlpha(alpha)
        self.__y = self.__s = None

    def __setAlpha(self, alpha):
        alpha = float(alpha)
        if alpha<=0 or alpha>1.0:
            raise ValueError("alpha (%s) should be in (0.0, 1.0]"%alpha)
        self.__alpha = alpha

    def __call__(self, value, timestamp=None, alpha=None):        
        if alpha is not None:
            self.__setAlpha(alpha)
        if self.__y is None:
            s = value
        else:
            s = self.__alpha*value + (1.0-self.__alpha)*self.__s
        self.__y = value
        self.__s = s
        return s

    def lastValue(self):
        return self.__y
