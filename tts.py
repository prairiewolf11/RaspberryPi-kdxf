def text_to_voice(text):
    """
    科大讯飞离线语音合成
    :param text: 转换文本
    开发API文档：http://mscdoc.xfyun.cn/windows/api/iFlytekMSCReferenceManual/files.html
    API调用流程：https://doc.xfyun.cn/msc_windows/%E8%AF%AD%E9%9F%B3%E5%90%88%E6%88%90.html
    LoadLibrary： 将指定的模块加载到调用进程的地址空间中（C++）
    MSPLogin： 初始化msc，用户登录
    QTTSSessionBegin： 开始一次语音合成，分配语音合成资源
    QTTSTextPut： 写入要合成的文本
    QTTSAudioGet： 获取合成音频
    QTTSSessionEnd： 结束本次语音合成
    MSPLogout:  退出登录
    :return:
    """
    try:
        # 此方法引用：windows/ubuntu/centos三种环境均测试过，可以调用
        from ctypes import cdll, c_int, byref, string_at
    except Exception as e:
        return e
    try:
        # 该配置文件需要放到python安装目录下，否则会报错(如果不在该目录，则需要单独配置环境变量)
        msc_load_library = config.get_MSC_LOAD_LIBRARY()  # 这里的config是增加了另一层封装，没有粘出代码来，下面的代码会配上配置文件中的格式，只要对应的把配置文件中的内容替换到这里就可以了。
        app_id = "56ee43d0"
        work_dir = "."
        voice_name = config.get_VOICE_NAME()
        login_tts_res_path = config.get_LOGIN_TTS_RES_PATH()
        session_tts_res_path = config.get_SESSION_TTS_RES_PATH()
    except Exception as e:
        return e
 
    frame_rate = 8000  # 频率
    MSP_SUCCESS = 0
    MSP_TTS_FLAG_STILL_HAVE_DATA = 1
    MSP_TTS_FLAG_DATA_END = 2  # 结束标识
    MSP_TTS_FLAG_CMD_CANCELED = 4
 
    login_params = "appid=%s, engine_start=tts, tts_res_path=%s, work_dir=%s" % (app_id, login_tts_res_path, work_dir)
    session_begin_params = b"engine_type=local, voice_name=%s, text_encoding=utf8, tts_res_path=%s, sample_rate=8000, speed=80, volume=50, pitch=50, rdn=2, effect=0, speed_increase=1, rcn=1" % ( voice_name, session_tts_res_path)
    dll = cdll.LoadLibrary(msc_load_library)
    ret = dll.MSPLogin(None, None, login_params)
    # print ret
    errorCode, audio_len, synth_status, getret = c_int(), c_int(), c_int(), c_int()
    sessionID = dll.QTTSSessionBegin(session_begin_params, byref(errorCode))
    # print sessionID
    # text_s = text.encode()
    text_s = text  # 测试代码
    string = text_s.replace("(", "（").replace(")", "）")
    string = string.replace("[", "【").replace("]", "】")
    ret = dll.QTTSTextPut(sessionID, ctypes.c_char_p(string), len(string), None)
    # print ret
    # 1、打开WAV文档
    wavFile = wave.open(r"tts_voice.wav", "wb")
    # 2、配置声道数、量化位数和取样频率
    wavFile.setnchannels(1)
    wavFile.setsampwidth(2)
    wavFile.setframerate(frame_rate)
    start_time = get_this_time()
    while True:
        end_time = get_this_time()
        print (end_time - start_time).seconds
        pdata = dll.QTTSAudioGet(sessionID, byref(audio_len),
                                 byref(synth_status), byref(getret))
        # print getret.value
        if getret.value != MSP_SUCCESS:
            break
        if pdata:
            data = string_at(pdata, audio_len.value)
            # 3、将wav_data转换为二进制数据写入文件
            wavFile.writeframes(data)
        if synth_status.value == MSP_TTS_FLAG_DATA_END:
            break
        time.sleep(0.1)  # 这里为官方建议，可以去除不使用，避免转换时间过长
    # 4、关闭文件
    wavFile.close()
    ret = dll.QTTSSessionEnd(sessionID, "Normal")
    dll.MSPLogout()
