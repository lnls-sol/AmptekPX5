from AmptekLib import AmptekPX5
from sardana.macroserver.macro import Type, Macro, ParamRepeat



class AmptekMacro(object):
    FIRST_SCA = 1
    LAST_SCA = 7
    def initAmptek(self, config=False):
        try:
            dev_name = self.getEnv('AmptekPx5Device')
            nr_tries = self.getEnv('AmptekPx5Tries')
        except Exception,e:
            msg = ('The macro needs two enviroment variables to work '
                   'AmptekPx5Device (device host) and AmptekPx5Tries (number of '
                   'tries to communicate with the HW)')
            raise RuntimeError(msg)
        self.amptek = AmptekPX5(dev_name, timeout=2.5, nr_tries=nr_tries)
        if not config:
            self.readRois()
      
    def readRois(self):
        self._rois=[]
        cmd = ''
        for i in range(self.FIRST_SCA, self.LAST_SCA+1):
            cmd += 'SCAI=%d;SCAL;SCAH;' %(i+1)
        self.debug('Asking to Device...')
        
        data = self.amptek.readTextConfig(cmd)

        values = [value.split('=')[1] 
                  for index,value in enumerate(data[:-1].split(';')) 
                  if index not in (0,3,6,9,12,15,18)]
        for i in range(self.FIRST_SCA, self.LAST_SCA+1):
            low = int(values[2*i-2])
            high = int(values[2*i-1])
            self._rois.append([low, high])
            
    def setRoi(self, roi, minim=0, maximum=8191):
        self._rois[roi-1] = [minim, maximum]
    
    def getRoi(self, roi):
        return self._rois[roi-1]
    
    def writeRois(self):
        #Configure the ICR and the first SCA as TCR
        cmd = ('AUO1=ICR;CON1=AUXOUT1;SCAI=1;SCAL=0;SCAH=8191;'
               'SCAO=HIGH;SCAW=100;')
        for i in range(self.FIRST_SCA, self.LAST_SCA+1):
            minim = self._rois[i-1][0]
            maxim = self._rois[i-1][1]
            cmd += ('SCAI=%d;SCAL=%d;SCAH=%d;SCAO=HIGH;SCAW=100;' 
                    %(i+1, minim, maxim))
        self.debug('Command to write values in Device: %s' % cmd)
        self.amptek.writeTextConfig(cmd)
        self.readRois()
    
    def readConfig(self, keys):
        config = {}
        cmd = ''
        for key in keys:
            cmd += '%s;' % key
        self.debug('Command to read configuration: %s' % cmd)
        data = self.amptek.readTextConfig(cmd)
        self.debug('Answer of read configuration: %s' % data)
        values = data.split(';')[:-1]
        for value in values:
            k, v = value.split('=')
            config[k]=v
        return config
    
    def writeConfig(self, config={}):
        if len(config.keys()) == 0:
            return
        keys = config.keys()
        keys.sort()
        cmd = ''
        for key in keys:
            cmd += '%s=%s;' %(key.upper(),config[key])
        self.debug('')
        self.amptek.writeTextConfig(cmd)
        
 

class amptekRois(Macro,AmptekMacro):
    """
    This macro configure the Amptek ROIs from the 1th to 7th hardware
    ROIs. 
    
    If you don't pass any parameter the macro shows you the current 
    configuration. 
    
    """
    #There is only for SCA connected to the NI6601 and it is the same as the GUI
    LAST_SCA=4
    param_def = [
        ['sca_list',ParamRepeat(['Number', Type.Integer, None, 'SCA channel'],
                     ['Low_Value', Type.Integer, None, 'Low threshold '],
                     ['High_Value', Type.Integer, None, 'High threshold'],
                     min=0, max=6), None, 
         'List of SCA configuration, example: sca1 100 800']]

    
    def run(self, *sca_list):
        self.initAmptek()
        if sca_list is not None:
            for index, low_value, high_value in sca_list:
                if index<0 or low_value<0 or high_value<0:
                    raise ValueError('The values must be positive')
                if low_value >= high_value:
                    raise
                self.setRoi(index, low_value, high_value)
            self.info('Setting SCAs...')
            self.writeRois()
 
        self.info('SCAs configuration')
        for i in range(self.FIRST_SCA, self.LAST_SCA+1):
            low, high = self.getRoi(i)
            msg = 'ROI%d: [%d, %d]' % (i,low, high)
            self.info(msg)
       
   

class amptekConf(Macro,AmptekMacro):
    """
    This macro configure the Amptek parameters:
    * Course Gain (GAIN)  
    * Peaking Time (PT)  
    * Low threshold (BGR)
    * Number of channels (MCAC): 512, 1024, 2046, 4096, 8192
      
    
    If you don't pass any parameter the macro shows you the current 
    configuration. 
    
    """
    PARAMS_CMD ={'GAIN':'GAIN',
                 'PT':'TPEA',
                 'MCAC':'MCAC',
                 'BGR': 'THSL'}
    param_def = [
        ['param_list',ParamRepeat(['Param', Type.String, None, 
                                   ('Name of the parameter (GAIN, MCAC, '
                                    'PT and BGD)')],
                                  ['Value', Type.Float, None, 'Value '],
                                  min=0, max=4), 
        None, 'List of parameters, example: sca1 100 800']]
    
    def prepare(self, *args):
        self.CMD_PARAMS = {}
        for param, cmd in self.PARAMS_CMD.items():
            self.CMD_PARAMS[cmd] = param
            
    def run(self, *param_list):
        self.initAmptek(True)
        if param_list is not None:
            param_allow = self.PARAMS_CMD.keys()
            new_config = {}
            for param, value in param_list:
                param = param.upper()
                if param not in param_allow:
                    raise ValueError('The allower paramters are: %s' % 
                                     repr(param_allow))
                cmd = self.PARAMS_CMD[param]    
                new_config[cmd] = value 
            self.info('Setting configuration....')
            self.writeConfig(new_config)
        
        config = self.readConfig(self.CMD_PARAMS.keys())
        self.info('Amptek configuration')
        for cmd, value in config.items():
            msg = '%s: %s' % (self.CMD_PARAMS[cmd], value)
            self.info(msg)
            
    