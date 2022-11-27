from enum import Enum

_SpeechSynthesisOutputFormat: dict[int,str] = {
    1:  'raw-8khz-8bit-mono-mulaw',
    2:  'riff-16khz-16kbps-mono-siren',
    3:  'audio-16khz-16kbps-mono-siren',
    4:  'audio-16khz-32kbitrate-mono-mp3',
    5:  'audio-16khz-128kbitrate-mono-mp3',
    6:  'audio-16khz-64kbitrate-mono-mp3',
    7:  'audio-24khz-48kbitrate-mono-mp3',
    8:  'audio-24khz-96kbitrate-mono-mp3',
    9:  'audio-24khz-160kbitrate-mono-mp3',
    10: 'raw-16khz-16bit-mono-truesilk',
    11: 'riff-16khz-16bit-mono-pcm',
    12: 'riff-8khz-16bit-mono-pcm',
    13: 'riff-24khz-16bit-mono-pcm',
    14: 'riff-8khz-8bit-mono-mulaw',
    15: 'raw-16khz-16bit-mono-pcm',
    16: 'raw-24khz-16bit-mono-pcm',
    17: 'raw-8khz-16bit-mono-pcm',
    18: 'ogg-16khz-16bit-mono-opus',
    19: 'ogg-24khz-16bit-mono-opus',
    20: 'raw-48khz-16bit-mono-pcm',
    21: 'riff-48khz-16bit-mono-pcm',
    22: 'audio-48khz-96kbitrate-mono-mp3',
    23: 'audio-48khz-192kbitrate-mono-mp3',
    24: 'ogg-48khz-16bit-mono-opus',
    25: 'webm-16khz-16bit-mono-opus',
    26: 'webm-24khz-16bit-mono-opus',
    27: 'raw-24khz-16bit-mono-truesilk',
    28: 'raw-8khz-8bit-mono-alaw',
    29: 'riff-8khz-8bit-mono-alaw',
    30: 'webm-24khz-16bit-24kbps-mono-opus',
    31: 'audio-16khz-16bit-32kbps-mono-opus',
    32: 'audio-24khz-16bit-48kbps-mono-opus',
    33: 'audio-24khz-16bit-24kbps-mono-opus',
    34: 'raw-22050hz-16bit-mono-pcm',
    35: 'riff-22050hz-16bit-mono-pcm',
    36: 'raw-44100hz-16bit-mono-pcm',
    37: 'riff-44100hz-16bit-mono-pcm',
    38: 'amr-wb-16000hz'
}


class SpeechSynthesisOutputFormat(Enum):
    """
    Defines the possible speech synthesis output audio formats.
    """

    Raw8Khz8BitMonoMULaw = 1
    """
    raw-8khz-8bit-mono-mulaw
    """

    Riff16Khz16KbpsMonoSiren = 2
    """
    riff-16khz-16kbps-mono-siren
    Unsupported by the service. Do not use this value.
    """

    Audio16Khz16KbpsMonoSiren = 3
    """
    audio-16khz-16kbps-mono-siren
    Unsupported by the service. Do not use this value.
    """

    Audio16Khz32KBitRateMonoMp3 = 4
    """
    audio-16khz-32kbitrate-mono-mp3
    """

    Audio16Khz128KBitRateMonoMp3 = 5
    """
    audio-16khz-128kbitrate-mono-mp3
    """

    Audio16Khz64KBitRateMonoMp3 = 6
    """
    audio-16khz-64kbitrate-mono-mp3
    """

    Audio24Khz48KBitRateMonoMp3 = 7
    """
    audio-24khz-48kbitrate-mono-mp3
    """

    Audio24Khz96KBitRateMonoMp3 = 8
    """
    audio-24khz-96kbitrate-mono-mp3
    """

    Audio24Khz160KBitRateMonoMp3 = 9
    """
    audio-24khz-160kbitrate-mono-mp3
    """

    Raw16Khz16BitMonoTrueSilk = 10
    """
    raw-16khz-16bit-mono-truesilk
    """

    Riff16Khz16BitMonoPcm = 11
    """
    riff-16khz-16bit-mono-pcm
    """

    Riff8Khz16BitMonoPcm = 12
    """
    riff-8khz-16bit-mono-pcm
    """

    Riff24Khz16BitMonoPcm = 13
    """
    riff-24khz-16bit-mono-pcm
    """

    Riff8Khz8BitMonoMULaw = 14
    """
    riff-8khz-8bit-mono-mulaw
    """

    Raw16Khz16BitMonoPcm = 15
    """
    raw-16khz-16bit-mono-pcm
    """

    Raw24Khz16BitMonoPcm = 16
    """
    raw-24khz-16bit-mono-pcm
    """

    Raw8Khz16BitMonoPcm = 17
    """
    raw-8khz-16bit-mono-pcm
    """

    Ogg16Khz16BitMonoOpus = 18
    """
    ogg-16khz-16bit-mono-opus
    """

    Ogg24Khz16BitMonoOpus = 19
    """
    ogg-24khz-16bit-mono-opus
    """

    Raw48Khz16BitMonoPcm = 20
    """
    raw-48khz-16bit-mono-pcm
    """

    Riff48Khz16BitMonoPcm = 21
    """
    riff-48khz-16bit-mono-pcm
    """

    Audio48Khz96KBitRateMonoMp3 = 22
    """
    audio-48khz-96kbitrate-mono-mp3
    """

    Audio48Khz192KBitRateMonoMp3 = 23
    """
    audio-48khz-192kbitrate-mono-mp3
    """

    Ogg48Khz16BitMonoOpus = 24
    """
    ogg-48khz-16bit-mono-opus
    """

    Webm16Khz16BitMonoOpus = 25
    """
    webm-16khz-16bit-mono-opus
    """

    Webm24Khz16BitMonoOpus = 26
    """
    webm-24khz-16bit-mono-opus
    """

    Raw24Khz16BitMonoTrueSilk = 27
    """
    raw-24khz-16bit-mono-truesilk
    """

    Raw8Khz8BitMonoALaw = 28
    """
    raw-8khz-8bit-mono-alaw
    """

    Riff8Khz8BitMonoALaw = 29
    """
    riff-8khz-8bit-mono-alaw
    """

    Webm24Khz16Bit24KbpsMonoOpus = 30
    """
    webm-24khz-16bit-24kbps-mono-opus
    Audio compressed by OPUS codec in a WebM container, with bitrate of 24kbps, optimized for IoT scenario.
    """

    Audio16Khz16Bit32KbpsMonoOpus = 31
    """
    audio-16khz-16bit-32kbps-mono-opus
    Audio compressed by OPUS codec without container, with bitrate of 32kbps.
    """

    Audio24Khz16Bit48KbpsMonoOpus = 32
    """
    audio-24khz-16bit-48kbps-mono-opus
    Audio compressed by OPUS codec without container, with bitrate of 48kbps.
    """

    Audio24Khz16Bit24KbpsMonoOpus = 33
    """
    audio-24khz-16bit-24kbps-mono-opus
    Audio compressed by OPUS codec without container, with bitrate of 24kbps.
    """

    Raw22050Hz16BitMonoPcm = 34
    """
    raw-22050hz-16bit-mono-pcm
    Raw PCM audio at 22050Hz sampling rate and 16-bit depth.
    """

    Riff22050Hz16BitMonoPcm = 35
    """
    riff-22050hz-16bit-mono-pcm
    PCM audio at 22050Hz sampling rate and 16-bit depth, with RIFF header.
    """

    Raw44100Hz16BitMonoPcm = 36
    """
    raw-44100hz-16bit-mono-pcm
    Raw PCM audio at 44100Hz sampling rate and 16-bit depth.
    """

    Riff44100Hz16BitMonoPcm = 37
    """
    riff-44100hz-16bit-mono-pcm
    PCM audio at 44100Hz sampling rate and 16-bit depth, with RIFF header.
    """

    AmrWb16000Hz = 38
    """
    amr-wb-16000hz
    AMR-WB audio at 16kHz sampling rate.
    """


class ResultReason(Enum):
    """
    Specifies the possible reasons a recognition result might be generated.
    """
    Canceled = 1
    """
    Indicates that the recognition was canceled. More details can be found using the CancellationDetails object.
    """

    SynthesizingAudio = 8
    """
    Indicates the synthesized audio result contains a non-zero amount of audio data
    """

    SynthesizingAudioCompleted = 9
    """
    Indicates the synthesized audio is now complete for this phrase.
    """

    SynthesizingAudioStarted = 12
    """
    Indicates the speech synthesis is now started
    """


class CancellationReason(Enum):
    """
    Defines the possible reasons a recognition result might be canceled.
    Unsupported reasons is removed.
    You can refer to `azure.cognitiveservices.speech.enums` for the left ones.
    """

    Error = 1
    """
    Indicates that an error occurred during speech recognition.
    """

    CancelledByUser = 3
    """
    Indicates that request was cancelled by the user.
    """


class CancellationErrorCode(Enum):
    """
    Defines error code in case that CancellationReason is Error.
    Unsupported error is removed.
    You can refer to `azure.cognitiveservices.speech.enums` for the left ones.
    """

    NoError = 0
    """
    No error.
    If CancellationReason is EndOfStream, CancellationErrorCode
    is set to NoError.
    """

    TooManyRequests = 3
    """
    Indicates that the number of parallel requests exceeded the number of allowed concurrent transcriptions for the subscription.
    """

    Forbidden = 4
    """
    Indicates that the free subscription used by the request ran out of quota.
    """

    ConnectionFailure = 5
    """
    Indicates a connection error.
    """

    ServiceTimeout = 6
    """
    Indicates a time-out error when waiting for response from service.
    """

    ServiceError = 7
    """
    Indicates that an error is returned by the service.
    """

    ServiceUnavailable = 8
    """
    Indicates that the service is currently unavailable.
    """

    RuntimeError = 9
    """
    Indicates an unexpected runtime error.
    """
