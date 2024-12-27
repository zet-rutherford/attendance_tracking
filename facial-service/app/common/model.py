from typing import List

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase

@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class LogUpload:
    ex_url_images: str = ''
    ex_trace_id: str = ''

@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class DetectionResult:
    coordinate: List
    score: float
    type: str
    version: str


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class RecognitionResult:
    engine: str
    score: float
    value: str
    version: str


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class PreprocessInfo:
    url: str
    version: str


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OCRResult:
    detection: DetectionResult
    recognition: RecognitionResult


# class OCRRequestSchema(Schema):
#     img_url = fields.Str(data_key='img_url')
#     types = fields.List(fields.Str, data_key='ocr_types')


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OCRField:
    type: str
    value: str
    details: List[OCRResult]


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class OCRResponse:
    fields: List[OCRField]
    preprocess: PreprocessInfo
    card_type: str
    card_type_score: str


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass
class Log:
    ex_trace_id: str = ''
    ex_msg_exception: str = ''
    ex_username: str = ''
    ex_feature: str = ''
    ex_image_align: str = ''
    ex_score_search: float = 0.0
    ex_score_matching: float = 0.0
    ex_time_decode_image: float = 0.0
    ex_time_detection: float = 0.0
    ex_time_extract_feature: float = 0.0
    ex_time_recognition: float = 0.0
    ex_download_fail_img_list: list = field(default_factory=list)
    ex_decode_fail_img_list: list = field(default_factory=list)
    ex_image_link: str = 'none'
    ex_downloading_image_time: str = ''
    # ex_downloading_image_response: str = 'OK'
    # ex_ocr_time: str = ''
    # ex_ocr_response: str = 'OK'

    lt: str = 'dbal'
    url: str = ''
    urp: str = ''
    urq: str = ''
    rt: float = 0.0
    st: int = 0
    mt: str = ''
    rmip: str = ''
    cip: str = ''
    bbs: int = 0
    cl: int = 0
    rf: str = ''
    ua: str = ''
    host: str = ''
    sn: str = ''
    tl: str = ''
    rid: str = ''
    uid: str = ''
    usrc: str = 'IAM'
