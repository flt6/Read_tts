from typing import Any, Callable, NoReturn, Optional, Union
from .enums import (SpeechSynthesisOutputFormat, ResultReason,
                   CancellationReason, CancellationErrorCode,
                   _SpeechSynthesisOutputFormat)
from xml.sax.saxutils import escape
from .tts import implete
import asyncio
from threading import Thread
from pydub import AudioSegment as audio
from pydub.playback import play
from io import BytesIO
from datetime import timedelta
from websockets.exceptions import InvalidStatus,InvalidHandshake
from traceback import format_exc
import nest_asyncio

nest_asyncio.apply()   # I'm wondering why this is needed for some time
                       # I wrote this due to https://stackoverflow.com/questions/46827007/runtimeerror-this-event-loop-is-already-running-in-python 

loop = asyncio.get_event_loop()

class AudioOutputStream():
    """
    Base class for Output Streams
    """


class AutoDetectSourceLanguageConfig:
    "Not implemented"


class ResultFuture():
    """
    The result of an asynchronous operation.
    """

    def __init__(self, task:asyncio.Task,handle:Callable[[bytes],Any]):
        """
        private constructor
        """
        self._task = task
        self._handle = handle
        self._thr = Thread(target=self._wait)
        self._thr.start()

    def _wait(self):
        global loop
        print("start waiting",self._task)
        try:
            self._ret = loop.run_until_complete(self._task)
        except Exception as e:
            with open("err_{}.log".format(self._task.get_name()),"a") as f:
                f.write(format_exc())
        self._handle(self._ret[1])
        print("done",self._task)
    
    def get(self):
        """
        Waits until the result is available, and returns it.
        """
        try:
            self._thr.join()
            ret = self._ret
        except Exception:
            ret = None
        exc = self._task.exception
        return SpeechSynthesisResult(ret,exc)  # type: ignore
                


class SpeechSynthesisCancellationDetails():
    """
    Contains detailed information about why a result was canceled.
    """

    def __init__(self, exc: BaseException):
        if isinstance(exc, KeyboardInterrupt):
            self.__reason = CancellationReason.CancelledByUser
            self.__error_code = CancellationErrorCode.NoError
        elif isinstance(exc, InvalidStatus):
            self.__reason = CancellationReason.Error
            code = exc.response.status_code
            if code == 429:
                self.__error_code = CancellationErrorCode.TooManyRequests
            elif code == 403:
                self.__error_code = CancellationErrorCode.Forbidden
            elif code == 500:
                self.__error_code = CancellationErrorCode.ServiceError
            elif code == 503:
                self.__error_code = CancellationErrorCode.ServiceUnavailable
            else:
                self.__error_code = CancellationErrorCode.RuntimeError
        elif isinstance(exc, InvalidHandshake):
            self.__reason = CancellationReason.Error
            self.__error_code = CancellationErrorCode.ConnectionFailure
        elif isinstance(exc,TimeoutError):
            self.__reason = CancellationReason.Error
            self.__error_code = CancellationErrorCode.ServiceTimeout
        else:
            self.__reason = CancellationReason.Error
            self.__error_code = CancellationErrorCode.RuntimeError
        self.__error_details = NotImplemented

    @property
    def reason(self) -> CancellationReason:
        """
        The reason the result was canceled.
        """
        return self.__reason

    @property
    def error_code(self) -> CancellationErrorCode:
        """
        The error code in case of an unsuccessful speech synthesis (Reason is set to Error).
        If Reason is not Error, ErrorCode is set to NoError.
        """
        return self.__error_code

    @property
    def error_details(self) -> str:
        """
        The error message in case of an unsuccessful speech synthesis (Reason is set to Error)
        """
        raise NotImplementedError("`error_details` is not implemented. (Maybe available in recent future)")
        return self.__error_details


class SpeechSynthesisResult():
    """
    Result of a speech synthesis operation.
    """

    def __init__(self,ret:Union[tuple[str,bytes],None], exc:Union[BaseException,None]):
        """
        Constructor for internal use.
        """
        if exc is not None:
            self._reason = ResultReason.Canceled
            self._result_id = None
            self._audio_duration_milliseconds = None
            self._audio_data = None
            self._cancellation_details = SpeechSynthesisCancellationDetails(exc)
        else:
            assert ret is not None
            req_id, data = ret
            sound:audio = audio.from_file(BytesIO(data))
            self._reason = ResultReason.SynthesizingAudioCompleted
            self._result_id = req_id
            self._audio_duration_milliseconds = timedelta(seconds=sound.duration_seconds)
            self._audio_data = data
            self._cancellation_details = None

    @property
    def cancellation_details(self) -> Optional[SpeechSynthesisCancellationDetails]:
        """
        The reason why speech synthesis was cancelled.

        Returns `None` if there was no cancellation.
        """
        return self._cancellation_details

    @property
    def result_id(self) -> Optional[str]:
        """
        Synthesis result unique ID.
        Return `None` if cancelled.
        """
        return self._result_id

    @property
    def reason(self) -> "ResultReason":
        """
        Synthesis reason.
        """
        return self._reason

    @property
    def audio_data(self) -> Optional[bytes]:
        """
        The output audio data from the TTS.
        Return `None` if cancelled.
        """
        return self._audio_data

    @property
    def audio_duration(self) -> Optional[timedelta]:
        """
        The time duration of the synthesized audio.
        Return `None` if cancelled.

        .. note::
          Added in version 1.21.0.
        """
        return self._audio_duration_milliseconds

    @property
    def properties(self) -> NoReturn:
        """
        Unsupported
        """
        raise NotImplementedError("`properties` unsupported")

    def __str__(self):
        if self._audio_data is None:
            return u'{}(result_id={}, reason={})'.format(
            type(self).__name__, self._result_id, self._reason)
        return u'{}(result_id={}, reason={}, audio_length={})'.format(
            type(self).__name__, self._result_id, self._reason, len(self._audio_data))


class SpeechConfig():
    """
    Class that defines configurations for speech synthesis.
    Several configurations is not supported.
    """

    def __init__(self):
        self._speech_synthesis_language = ""
        self._speech_synthesis_voice_name = "zh-CN-XiaoxiaoNeural"
        self._speech_synthesis_output_format_string = "audio-24khz-48kbitrate-mono-mp3"

    @property
    def speech_synthesis_language(self) -> str:
        """
        **Not used. I'm wondering what this is for.**

        Get speech synthesis language.
        """
        return self._speech_synthesis_language

    @speech_synthesis_language.setter
    def speech_synthesis_language(self, language: str):
        """
        Set speech synthesis language.

        :param language: The language for speech synthesis (e.g. en-US).
        """
        self._speech_synthesis_language = language

    @property
    def speech_synthesis_voice_name(self) -> str:
        """
        Get speech synthesis voice name.
        """
        return self._speech_synthesis_voice_name

    @speech_synthesis_voice_name.setter
    def speech_synthesis_voice_name(self, voice: str):
        """
        Set speech synthesis voice name.

        :param voice: The name of voice for speech synthesis.
        """
        self._speech_synthesis_voice_name = voice

    @property
    def speech_synthesis_output_format_string(self) -> str:
        """
        Get speech synthesis output audio format string.
        """
        return self._speech_synthesis_output_format_string

    def set_speech_synthesis_output_format(self, format_id: SpeechSynthesisOutputFormat):
        """
        Set speech synthesis output audio format.

        :param format_id: The audio format id, e.g. Riff16Khz16BitMonoPcm.
        """
        if not isinstance(format_id, SpeechSynthesisOutputFormat):
            raise TypeError('wrong type, must be SpeechSynthesisOutputFormat')
        self._speech_synthesis_output_format_string = _SpeechSynthesisOutputFormat[format_id.value]


class AudioOutputConfig():
    """
    Copied from azure.cognitiveservices.speech.audio
    Represents specific audio configuration, such as audio output device, file, or custom audio streams

    Generates an audio configuration for the speech synthesizer. Only one argument can be
    passed at a time.

    :param use_default_speaker: Specifies to use the system default speaker for audio
        output.
    :param filename: Specifies an audio output file. The parent directory must already exist.
    [UNSUPPORT]:param stream: Creates an AudioOutputConfig object representing the specified stream.
    :param device_name: Specifies the id of the audio device to use.
         This functionality was added in version 1.17.0.
    """

    def __init__(self, use_default_speaker: Optional[bool] = False, filename: Optional[str] = None,
                 stream: Optional[AudioOutputStream] = None, device_name: Optional[str] = None):
        if not isinstance(use_default_speaker, bool):
            raise ValueError('use_default_speaker must be a bool, is "{}"'.format(
                use_default_speaker))
        if stream is not None:
            raise NotImplementedError("`stream` has not been implemented")
        if filename is None and stream is None and device_name is None:
            if use_default_speaker:
                # Default speaker
                self.handle = lambda b:play(audio.from_file(BytesIO(b)))
            else:
                raise ValueError(
                    'default speaker needs to be explicitly activated')
        else:
            if sum(x is not None for x in (filename, stream, device_name)) > 1:
                raise ValueError(
                    'only one of filename, stream, and device_name can be given')

            if filename is not None:
                # filename
                def _handle(byte):
                    with open(filename,"wb") as f:
                        f.write(byte)
                self.handle = _handle
            elif stream is not None:
                pass
                # self._stream = stream
                # _call_hr_fn(fn=_sdk_lib.audio_config_create_audio_output_from_stream,
                #             *[ctypes.byref(handle), stream._handle])
            elif device_name is not None:
                # detected device name
                raise NotImplementedError("Due to pydub.playback doesn't support choosing device, `device_name` may not be supported.")
            else:
                raise ValueError(
                    'cannot construct AudioOutputConfig with the given arguments')


class SpeechSynthesizer:
    """
    A speech synthesizer.

    :param speech_config: The config for the speech synthesizer
    :param audio_config: The config for the audio output.
        This parameter is optional.
        If it is not provided, the default speaker device will be used for audio output.
        If it is None, the output audio will be dropped.
        None can be used for scenarios like performance test.
    [NOTSUPPORT]:param auto_detect_source_language_config: The auto detection source language config
    """

    def __init__(self, speech_config: SpeechConfig,
                 audio_config: Optional[AudioOutputConfig] = AudioOutputConfig(
                     use_default_speaker=True),
                 auto_detect_source_language_config: Optional[AutoDetectSourceLanguageConfig] = None):

        self._speech_config = speech_config
        self._audio_config:AudioOutputConfig = audio_config  # type: ignore
        if auto_detect_source_language_config is not None:
            raise NotImplementedError(
                'auto_detect_source_language_config is not supported')

    def _build_ssml(self, text: str) -> str:
        """
        Copied from aspeak.ssml
        Create SSML for text to be spoken.
        """
        voice = self._speech_config.speech_synthesis_voice_name
        ssml = '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" ' \
            'xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"> '
        ssml += f'<voice name="{voice}">' if voice is not None else '<voice>'
        ssml += escape(text)
        ssml += '</voice></speak>'
        return ssml

    def speak_text(self, text: str) -> SpeechSynthesisResult:
        """
        Performs synthesis on plain text in a blocking (synchronous) mode.

        :returns: A SpeechSynthesisResult.
        """
        return self.speak_text_async(text).get()

    def speak_ssml(self, ssml: str) -> SpeechSynthesisResult:
        """
        Performs synthesis on ssml in a blocking (synchronous) mode.

        :returns: A SpeechSynthesisResult.
        """
        return self.speak_ssml_async(ssml).get()

    def speak_text_async(self, text: str) -> ResultFuture:
        """
        Performs synthesis on plain text in a non-blocking (asynchronous) mode.

        :returns: A future with SpeechSynthesisResult.
        """
        ssml = self._build_ssml(text)
        task = asyncio.get_event_loop().create_task(implete(ssml,self._speech_config.speech_synthesis_output_format_string))
        print("Created task: ",task)
        return ResultFuture(task,self._audio_config.handle)

    def speak_ssml_async(self, ssml: str) -> ResultFuture:
        """
        Performs synthesis on ssml in a non-blocking (asynchronous) mode.

        :returns: A future with SpeechSynthesisResult.
        """
        task = asyncio.get_event_loop().create_task(implete(ssml,self._speech_config.speech_synthesis_output_format_string))
        return ResultFuture(task,self._audio_config.handle)

    def start_speaking_text(self, text: str) -> SpeechSynthesisResult:
        """
        Starts synthesis on plain text in a blocking (synchronous) mode.

        :returns: A SpeechSynthesisResult.
        """
        return self.start_speaking_text_async(text).get()

    def start_speaking_ssml(self, ssml: str) -> SpeechSynthesisResult:
        """
        Starts synthesis on ssml in a blocking (synchronous) mode.

        :returns: A SpeechSynthesisResult.
        """
        return self.start_speaking_ssml_async(ssml).get()

    def start_speaking_text_async(self, text: str) -> ResultFuture:
        """
        Starts synthesis on plain text in a non-blocking (asynchronous) mode.

        I'm wondering the difference between this and `speak_ssml_async`,
        I've made this the same as `speak_ssml_async`. If anyone knows that, pleaes pull an Issue.
        :returns: A future with SpeechSynthesisResult.
        """
        return self.speak_text_async(text)

    def start_speaking_ssml_async(self, ssml: str) -> ResultFuture:
        """
        Starts synthesis on ssml in a non-blocking (asynchronous) mode.

        I'm wondering the difference between this and `speak_ssml_async`,
        I've made this the same as `speak_ssml_async`. If anyone knows that, pleaes pull an Issue.
        :returns: A future with SpeechSynthesisResult.
        """
        return self.speak_ssml_async(ssml)

    def stop_speaking_async(self):
        """
        **Not Support**

        Asynchronously terminates ongoing synthesis operation.
        This method will stop playback and clear unread data in PullAudioOutputStream.

        :returns: A future that is fulfilled once synthesis has been stopped.
        """
        raise NotImplementedError("This method wasn't support.")
        async_handle = _spx_handle(0)
        _call_hr_fn(fn=_sdk_lib.synthesizer_stop_speaking_async,
                    *[self._handle, ctypes.byref(async_handle)])

        def resolve_future(handle: _spx_handle):
            _call_hr_fn(
                fn=_sdk_lib.synthesizer_stop_speaking_async_wait_for, *[handle, max_uint32])
            _sdk_lib.synthesizer_async_handle_release(handle)
            return None
        return ResultFuture(async_handle, resolve_future, None)

    def stop_speaking(self):
        """
        **Not Support**

        Synchronously terminates ongoing synthesis operation.
        This method will stop playback and clear unread data in PullAudioOutputStream.
        """
        self.stop_speaking_async().get()

    def get_voices_async(self, locale: str = "") -> ResultFuture:
        """
        **Not Support**

        Get the available voices, asynchronously.

        :param locale: Specify the locale of voices, in BCP-47 format; or leave it empty to get all available voices.
        :returns: A task representing the asynchronous operation that gets the voices.
        """
        raise NotImplementedError("This method wasn't support. You can get this through `azure.cognitiveservices.speech`")
        async_handle = _spx_handle(0)
        c_locale = _c_str(locale)
        _call_hr_fn(fn=_sdk_lib.synthesizer_get_voices_list_async,
                    *[self._handle, c_locale, ctypes.byref(async_handle)])

        def resolve_future(handle: _spx_handle):
            result_handle = _spx_handle(0)
            _call_hr_fn(fn=_sdk_lib.synthesizer_get_voices_list_async_wait_for,
                        *[handle, max_uint32, ctypes.byref(result_handle)])
            _sdk_lib.synthesizer_async_handle_release(handle)
            return result_handle
        return ResultFuture(async_handle, resolve_future, SynthesisVoicesResult)

    @property
    def properties(self) -> NoReturn:
        """
        A collection of properties and their values defined for this SpeechSynthesizer.
        """
        raise NotImplementedError("This method wasn't support since most of it is implemented in C++.")
        # return self.__properties

    # @property
    # def synthesis_started(self) -> EventSignal:
    #     """
    #     Signal for events indicating synthesis has started.

    #     Callbacks connected to this signal are called with a :class:`.SpeechSynthesisEventArgs`
    #     instance as the single argument.
    #     """
    #     def synthesis_started_connection(signal: EventSignal, handle: _spx_handle):
    #         callback = SpeechSynthesizer.__synthesis_started_callback if signal.is_connected() else None
    #         _sdk_lib.synthesizer_started_set_callback(
    #             handle, callback, signal._context_ptr)
    #     if self.__synthesis_started_signal is None:
    #         self.__synthesis_started_signal = EventSignal(
    #             self, synthesis_started_connection)
    #     return self.__synthesis_started_signal

    # @ctypes.CFUNCTYPE(None, _spx_handle, _spx_handle, ctypes.c_void_p)
    # def __synthesis_started_callback(reco_handle: _spx_handle, event_handle: _spx_handle, context: ctypes.c_void_p):
    #     event_handle = _spx_handle(event_handle)
    #     obj = _unpack_context(context)
    #     if obj is not None:
    #         event = SpeechSynthesisEventArgs(event_handle)
    #         obj.__synthesis_started_signal.signal(event)

    # __synthesizing_signal = None

    # @property
    # def synthesizing(self) -> EventSignal:
    #     """
    #     Signal for events indicating synthesis is ongoing.

    #     Callbacks connected to this signal are called with a :class:`.SpeechSynthesisEventArgs`
    #     instance as the single argument.
    #     """
    #     def synthesizing_connection(signal: EventSignal, handle: _spx_handle):
    #         callback = SpeechSynthesizer.__synthesizing_callback if signal.is_connected() else None
    #         _sdk_lib.synthesizer_synthesizing_set_callback(
    #             handle, callback, signal._context_ptr)
    #     if self.__synthesizing_signal is None:
    #         self.__synthesizing_signal = EventSignal(
    #             self, synthesizing_connection)
    #     return self.__synthesizing_signal

    # @ctypes.CFUNCTYPE(None, _spx_handle, _spx_handle, ctypes.c_void_p)
    # def __synthesizing_callback(reco_handle: _spx_handle, event_handle: _spx_handle, context: ctypes.c_void_p):
    #     event_handle = _spx_handle(event_handle)
    #     obj = _unpack_context(context)
    #     if obj is not None:
    #         event = SpeechSynthesisEventArgs(event_handle)
    #         obj.__synthesizing_signal.signal(event)

    # __synthesis_completed_signal = None

    # @property
    # def synthesis_completed(self) -> EventSignal:
    #     """
    #     Signal for events indicating synthesis has completed.

    #     Callbacks connected to this signal are called with a :class:`.SpeechSynthesisEventArgs`
    #     instance as the single argument.
    #     """
    #     def synthesis_completed_connection(signal: EventSignal, handle: _spx_handle):
    #         callback = SpeechSynthesizer.__synthesis_completed_callback if signal.is_connected() else None
    #         _sdk_lib.synthesizer_completed_set_callback(
    #             handle, callback, signal._context_ptr)
    #     if self.__synthesis_completed_signal is None:
    #         self.__synthesis_completed_signal = EventSignal(
    #             self, synthesis_completed_connection)
    #     return self.__synthesis_completed_signal

    # @ctypes.CFUNCTYPE(None, _spx_handle, _spx_handle, ctypes.c_void_p)
    # def __synthesis_completed_callback(reco_handle: _spx_handle, event_handle: _spx_handle, context: ctypes.c_void_p):
    #     event_handle = _spx_handle(event_handle)
    #     obj = _unpack_context(context)
    #     if obj is not None:
    #         event = SpeechSynthesisEventArgs(event_handle)
    #         obj.__synthesis_completed_signal.signal(event)

    # __synthesis_canceled_signal = None

    # @property
    # def synthesis_canceled(self) -> EventSignal:
    #     """
    #     Signal for events indicating synthesis has been canceled.

    #     Callbacks connected to this signal are called with a :class:`.SpeechSynthesisEventArgs`
    #     instance as the single argument.
    #     """
    #     def synthesis_canceled_connection(signal: EventSignal, handle: _spx_handle):
    #         callback = SpeechSynthesizer.__synthesis_canceled_callback if signal.is_connected() else None
    #         _sdk_lib.synthesizer_canceled_set_callback(
    #             handle, callback, signal._context_ptr)
    #     if self.__synthesis_canceled_signal is None:
    #         self.__synthesis_canceled_signal = EventSignal(
    #             self, synthesis_canceled_connection)
    #     return self.__synthesis_canceled_signal

    # @ctypes.CFUNCTYPE(None, _spx_handle, _spx_handle, ctypes.c_void_p)
    # def __synthesis_canceled_callback(reco_handle: _spx_handle, event_handle: _spx_handle, context: ctypes.c_void_p):
    #     event_handle = _spx_handle(event_handle)
    #     obj = _unpack_context(context)
    #     if obj is not None:
    #         event = SpeechSynthesisEventArgs(event_handle)
    #         obj.__synthesis_canceled_signal.signal(event)

    # __synthesis_word_boundary_signal = None

    # @property
    # def synthesis_word_boundary(self) -> EventSignal:
    #     """
    #     Signal for events indicating a word boundary.

    #     Callbacks connected to this signal are called with a :class:`.SpeechSynthesisWordBoundaryEventArgs`
    #     instance as the single argument.
    #     """
    #     def synthesis_word_boundary_connection(signal: EventSignal, handle: _spx_handle):
    #         callback = SpeechSynthesizer.__synthesis_word_boundary_callback if signal.is_connected() else None
    #         _sdk_lib.synthesizer_word_boundary_set_callback(
    #             handle, callback, signal._context_ptr)
    #     if self.__synthesis_word_boundary_signal is None:
    #         self.__synthesis_word_boundary_signal = EventSignal(
    #             self, synthesis_word_boundary_connection)
    #     return self.__synthesis_word_boundary_signal

    # @ctypes.CFUNCTYPE(None, _spx_handle, _spx_handle, ctypes.c_void_p)
    # def __synthesis_word_boundary_callback(reco_handle: _spx_handle, event_handle: _spx_handle, context: ctypes.c_void_p):
    #     event_handle = _spx_handle(event_handle)
    #     obj = _unpack_context(context)
    #     if obj is not None:
    #         event = SpeechSynthesisWordBoundaryEventArgs(event_handle)
    #         obj.__synthesis_word_boundary_signal.signal(event)

    # __viseme_received_signal = None

    # @property
    # def viseme_received(self) -> EventSignal:
    #     """
    #     Signal for events indicating a viseme is received.

    #     Callbacks connected to this signal are called with a :class:`.SpeechSynthesisVisemeEventArgs`
    #     instance as the single argument.

    #     .. note::
    #         Added in version 1.16.0.
    #     """
    #     def viseme_received_connection(signal: EventSignal, handle: _spx_handle):
    #         callback = SpeechSynthesizer.__viseme_received_callback if signal.is_connected() else None
    #         _sdk_lib.synthesizer_viseme_received_set_callback(
    #             handle, callback, signal._context_ptr)
    #     if self.__viseme_received_signal is None:
    #         self.__viseme_received_signal = EventSignal(
    #             self, viseme_received_connection)
    #     return self.__viseme_received_signal

    # @ctypes.CFUNCTYPE(None, _spx_handle, _spx_handle, ctypes.c_void_p)
    # def __viseme_received_callback(reco_handle: _spx_handle, event_handle: _spx_handle, context: ctypes.c_void_p):
    #     event_handle = _spx_handle(event_handle)
    #     obj = _unpack_context(context)
    #     if obj is not None:
    #         event = SpeechSynthesisVisemeEventArgs(event_handle)
    #         obj.__viseme_received_signal.signal(event)

    # __bookmark_reached_signal = None

    # @property
    # def bookmark_reached(self) -> EventSignal:
    #     """
    #     Signal for events indicating a bookmark is reached.

    #     Callbacks connected to this signal are called with a :class:`.SpeechSynthesisBookmarkEventArgs`
    #     instance as the single argument.

    #     .. note::
    #         Added in version 1.16.0.
    #     """
    #     def bookmark_reached_connection(signal: EventSignal, handle: _spx_handle):
    #         callback = SpeechSynthesizer.__bookmark_reached_callback if signal.is_connected() else None
    #         _sdk_lib.synthesizer_bookmark_reached_set_callback(
    #             handle, callback, signal._context_ptr)
    #     if self.__bookmark_reached_signal is None:
    #         self.__bookmark_reached_signal = EventSignal(
    #             self, bookmark_reached_connection)
    #     return self.__bookmark_reached_signal

    # @ctypes.CFUNCTYPE(None, _spx_handle, _spx_handle, ctypes.c_void_p)
    # def __bookmark_reached_callback(reco_handle: _spx_handle, event_handle: _spx_handle, context: ctypes.c_void_p):
    #     event_handle = _spx_handle(event_handle)
    #     obj = _unpack_context(context)
    #     if obj is not None:
    #         event = SpeechSynthesisBookmarkEventArgs(event_handle)
    #         obj.__bookmark_reached_signal.signal(event)
