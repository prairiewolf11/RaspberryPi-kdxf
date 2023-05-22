import ctypes
import wave
import time
from ctypes import cdll, c_int, byref, string_at
import os

BASEPATH=os.path.split(os.path.realpath(__file__))[0]

frame_rate = 8000                 # 频率
MSP_SUCCESS = 0                   # 成功标识
MSP_TTS_FLAG_STILL_HAVE_DATA = 1
MSP_TTS_FLAG_DATA_END = 2         # 结束标识
MSP_TTS_FLAG_CMD_CANCELED = 4
"""
LoadLibrary： 将指定的模块加载到调用进程的地址空间中（C++）
MSPLogin： 初始化msc，用户登录
QTTSSessionBegin： 开始一次语音合成，分配语音合成资源
QTTSTextPut： 写入要合成的文本
QTTSAudioGet： 获取合成音频
QTTSSessionEnd： 结束本次语音合成
MSPLogout:  退出登录
"""

# 登入科大讯飞离线语音合成SDK
def login(login_dll,login_params):
    dll=login_dll
    params=login_params
    # ret为0时，则登入成功
    ret=dll.MSPLogin(None, None, params)
    if ret!=MSP_SUCCESS:
        print("登入失败")
        print(ret)
    else:
        print("登入成功")
# 开始一次语音合成，分配语音合成资源
def QTTS_Session_Begin(login_dll,session_begin_params):
    ret_c = c_int(0)
    dll=login_dll
    # 将session_begin_params以指定的编码格式编码字符串，格式为utf-8
    session_begin_params_bytes = bytes(session_begin_params, 'UTF-8')
    # python中c语音int型
    error_code = c_int()
    # python中c语音char型
    dll.QTTSSessionBegin.restype = ctypes.c_char_p
    
    sessionID = dll.QTTSSessionBegin(session_begin_params_bytes, byref(error_code))
    if error_code.value!=0 :
        print(f'调用失败，错误码 {error_code.value}')
    else:
        print("调用成功")
    return sessionID
# 写入要合成的文本
def QTTS_Text_PUT(login_dll,session_ID,text):
    dll = login_dll
    # 将text以指定的编码格式编码字符串，格式为utf-8
    text = text.encode('UTF-8')
    ret = dll.QTTSTextPut(session_ID, text, len(text), None)
    if ret!=MSP_SUCCESS:
        print("文本写入失败")
    else:
        print("文本写入成功")
# 获取合成音频
def QTTS_Audio_Get(login_dll,session_ID,wavFile):
    audio_len, synth_status, getret = c_int(), c_int(), c_int()
    dll = login_dll
    dll.QTTSAudioGet.restype = ctypes.c_void_p
    pdata = bytes()
    while True:
        pdata = dll.QTTSAudioGet(session_ID, byref(audio_len),
                                 byref(synth_status), byref(getret))
        # print(getret.value)
        # print(synth_status.value)
        if getret.value != MSP_SUCCESS:
            break
        if pdata:
            data = string_at(pdata, audio_len.value)
            # 将wav_data转换为二进制数据写入文件
            wavFile.writeframes(data)

        if synth_status.value == MSP_TTS_FLAG_DATA_END:
            break
        time.sleep(0.1)  # 这里为官方建议，可以去除不使用，避免转换时间过长
    wavFile.close()
#结束本次语音合成
def QTTS_Session_End(login_dll,session_ID):
    dll = login_dll
    dll.QTTSSessionEnd(session_ID, "Normal")
    dll.MSPLogout()
def play(filename):
    import pygame
    pygame.mixer.init(frequency=16000)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True:
        continue
if __name__=='__main__':

    # 调用科大讯飞离线SDK
    login_dll = cdll.LoadLibrary("libmsc.so")
    
    # 账号登入
    login_params = b"appid = 56ee43d0, work_dir = ."
    # 参数填写，实际参数去以下官网
    #https: // www.xfyun.cn / doc / mscapi / Windows & Linux / wlapi.html  # qtts-h-%E8%AF%AD%E9%9F%B3%E5%90%88%E6%88%90
    session_begin_params="voice_name = aisxping, text_encoding = utf8, sample_rate = 8000, speed = 50, volume = 50, pitch = 50, rdn = 0"
    # 文本输入
    text=("科大讯飞语音合成")

    login(login_dll, login_params)

    session_ID=QTTS_Session_Begin(login_dll, session_begin_params)

    QTTS_Text_PUT(login_dll, session_ID, text)

    # 1、打开WAV文档
    wavFile = wave.open(r"yuyin_Y.wav", "wb")
    # 2、配置声道数、量化位数和取样频率
    wavFile.setnchannels(1)
    wavFile.setsampwidth(2)
    wavFile.setframerate(frame_rate)
    QTTS_Audio_Get(login_dll,session_ID,wavFile)
    QTTS_Session_End(login_dll, session_ID)
    play(r"yuyin_Y.wav")