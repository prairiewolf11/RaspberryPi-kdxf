import os
from ctypes import cdll, byref, string_at, c_voidp, CFUNCTYPE, c_char_p, c_uint64, c_int64
import time
from loguru import logger
import Recorder

def py_ivw_callback(sessionID, msg, param1, param2, info, userDate):
    # typedef int( *ivw_ntf_handler)( const char *sessionID, int msg, int param1, int param2, const void *info, void *userData );
    # 在此处编辑唤醒后的动作
    print("sessionID =>", sessionID)
    print("msg =>", msg)
    print("param1 =>", param1)
    print("param2 =>", param2)
    print("info =>", info)
    print("userDate =>", userDate)


CALLBACKFUNC = CFUNCTYPE(None, c_char_p, c_uint64,
                         c_uint64, c_uint64, c_voidp, c_voidp)
pCallbackFunc = CALLBACKFUNC(py_ivw_callback)


def ivw_wakeup():
    try:
        msc_load_library = r'libmsc.so'
        app_id = '56ee43d0'# 填写自己的app_id
        ivw_threshold = '0:1450'
        jet_path = os.getcwd()+r'\speechRecognition\ivw\bin\wakeupresource.jet'
        work_dir = 'fo|' + jet_path
    except Exception as e:
        return e

    # ret 成功码
    MSP_SUCCESS = 0

    dll = cdll.LoadLibrary(msc_load_library)
    errorCode = c_int64()
    sessionID = c_voidp()
    # MSPLogin
    Login_params = "appid={},engine_start=ivw".format(app_id)
    Login_params = bytes(Login_params, encoding="utf8")
    ret = dll.MSPLogin(None, None, Login_params)
    if MSP_SUCCESS != ret:
        logger.info("MSPLogin failed, error code is: %d", ret)
        return

    # QIVWSessionBegin
    Begin_params = "sst=wakeup,ivw_threshold={},ivw_res_path={}".format(
        ivw_threshold, work_dir)
    Begin_params = bytes(Begin_params, encoding="utf8")
    dll.QIVWSessionBegin.restype = c_char_p
    sessionID = dll.QIVWSessionBegin(None, Begin_params, byref(errorCode))
    if MSP_SUCCESS != errorCode.value:
        logger.info("QIVWSessionBegin failed, error code is: {}".format(
                    errorCode.value))
        return

    # QIVWRegisterNotify
    dll.QIVWRegisterNotify.argtypes = [c_char_p, c_voidp, c_voidp]
    ret = dll.QIVWRegisterNotify(sessionID, pCallbackFunc, None)
    if MSP_SUCCESS != ret:
        logger.info("QIVWRegisterNotify failed, error code is: {}".format(ret))
        return

    # QIVWAudioWrite
    recorder = Recorder.Recorder()
    dll.QIVWAudioWrite.argtypes = [c_char_p, c_voidp, c_uint64, c_int64]
    ret = MSP_SUCCESS
    logger.info("* start recording")
    while ret == MSP_SUCCESS:
        audio_data = b''.join(recorder.get_record_audio())
        audio_len = len(audio_data)
        ret = dll.QIVWAudioWrite(sessionID, audio_data, audio_len, 2)
    logger.info('QIVWAudioWrite ret =>{}', ret)
    logger.info("* done recording")
    recorder.__del__()


if __name__ == '__main__':
    ivw_wakeup()
