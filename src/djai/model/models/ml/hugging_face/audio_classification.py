"""DjAI Pre-Trained Hugging Face Audio Classifier Model class."""


import sys
from typing import Dict, List   # Py3.9+: use generic types
from typing import Union

from django.utils.functional import classproperty

from gradio.interface import Interface
from gradio.inputs import (Audio as AudioInput,
                           Slider as SliderInput)
from gradio.outputs import Label as LabelOutput

import numpy

from djai.model.apps import DjAIModelModuleConfig
from djai.util import PGSQL_IDENTIFIER_MAX_LEN

from .base import PreTrainedHuggingFaceTransformer

if sys.version_info >= (3, 9):
    from collections.abc import Sequence
else:
    from typing import Sequence


__all__: Sequence[str] = ('PreTrainedHuggingFaceAudioClassifier',)


AudioClassificationInputType = Union[numpy.ndarray, str]
AudioClassificationOutputType = Dict[str, float]


class PreTrainedHuggingFaceAudioClassifier(PreTrainedHuggingFaceTransformer):
    # pylint: disable=abstract-method,too-many-ancestors
    """DjAI Pre-Trained Hugging Face Audio Classifier Model class."""

    class Meta(PreTrainedHuggingFaceTransformer.Meta):
        # pylint: disable=too-few-public-methods
        """Django Model Class Metadata."""

        verbose_name: str = 'Pre-Trained Hugging Face Audio Classifier'
        verbose_name_plural: str = 'Pre-Trained Hugging Face Audio Classifiers'

        db_table: str = (f'{DjAIModelModuleConfig.label}_'
                         f"{__qualname__.split(sep='.', maxsplit=1)[0]}")
        assert len(db_table) <= PGSQL_IDENTIFIER_MAX_LEN, \
            ValueError(f'*** "{db_table}" DB TABLE NAME TOO LONG ***')

        default_related_name: str = 'pretrained_hugging_face_audio_classifiers'

    def predict(self,
                audio_or_audios:
                    Union[AudioClassificationInputType,
                          Sequence[AudioClassificationInputType]],
                n_labels: int = 5) \
            -> Union[AudioClassificationOutputType,
                     List[AudioClassificationOutputType]]:
        # pylint: disable=arguments-differ
        """Classify Audio(s)."""
        single_audio: bool = isinstance(audio_or_audios, (numpy.ndarray, str))

        if not (single_audio or isinstance(audio_or_audios, list)):
            audio_or_audios: List[AudioClassificationInputType] = \
                list(audio_or_audios)

        self.load()

        output = self.native_obj(inputs=audio_or_audios, top_k=n_labels)

        return ({i['label']: i['score'] for i in output}
                if single_audio
                else [{i['label']: i['score'] for i in result}
                      for result in output])

    @classproperty
    def gradio_ui(cls) -> Interface:   # noqa: N805
        # pylint: disable=no-self-argument
        """Gradio Interface."""
        def _predict(self,
                     sampling_rate_and_double_channel_audio_array:
                     tuple[int, numpy.ndarray],
                     n_labels: int = 5) -> Dict[str, float]:
            _sampling_rate, double_channel_audio_array = \
                sampling_rate_and_double_channel_audio_array

            return cls.predict(
                self,
                audio_or_audios=(double_channel_audio_array[:, 0]
                                 .astype(numpy.float32)),
                n_labels=n_labels)

        return Interface(
            fn=_predict,
            # (Callable) - the function to wrap an interface around.

            inputs=[AudioInput(source='upload',
                               type='numpy',
                               label='Audio to Classify',
                               optional=False),

                    SliderInput(minimum=3, maximum=10, step=1, default=5,
                                label='No. of Labels to Return')],
            # (Union[str, List[Union[str, InputComponent]]]) -
            # a single Gradio input component,
            # or list of Gradio input components.
            # Components can either be passed as instantiated objects,
            # or referred to by their string shortcuts.
            # The number of input components should match
            # the number of parameters in fn.

            outputs=LabelOutput(num_top_classes=10,
                                type='auto',
                                label='Audio Classification'),
            # (Union[str, List[Union[str, OutputComponent]]]) -
            # a single Gradio output component,
            # or list of Gradio output components.
            # Components can either be passed as instantiated objects,
            # or referred to by their string shortcuts.
            # The number of output components should match
            # the number of values returned by fn.

            verbose=True,
            # (bool) - whether to print detailed information during launch.

            examples=None,
            # (Union[List[List[Any]], str]) - sample inputs for the function;
            # if provided, appears below the UI components and can be used
            # to populate the interface.
            # Should be nested list, in which the outer list consists of
            # samples and each inner list consists of an input
            # corresponding to each input component.
            # A string path to a directory of examples can also be provided.
            # If there are multiple input components and a directory
            # is provided, a log.csv file must be present in the directory
            # to link corresponding inputs.

            examples_per_page=10,
            # (int) - If examples are provided, how many to display per page.

            live=False,
            # (bool) - should the interface automatically reload on change?

            layout='unaligned',
            # (str) - Layout of input and output panels.
            # - "horizontal" arranges them as two columns of equal height,
            # - "unaligned" arranges them as two columns of unequal height, and
            # - "vertical" arranges them vertically.

            show_input=True,
            show_output=True,

            capture_session=False,
            # (bool) - if True, captures the default graph and session
            # (needed for Tensorflow 1.x)

            interpretation='default',
            # (Union[Callable, str]) - function that provides interpretation
            # explaining prediction output.
            # Pass "default" to use built-in interpreter.

            num_shap=2.0,
            # (float) - a multiplier that determines how many examples
            # are computed for shap-based interpretation.
            # Increasing this value will increase shap runtime,
            # but improve results.

            theme='default',
            # (str) - Theme to use - one of
            # - "default",
            # - "compact",
            # - "huggingface", or
            # - "darkhuggingface".

            repeat_outputs_per_model=True,

            title=cls._meta.verbose_name,
            # (str) - a title for the interface;
            # if provided, appears above the input and output components.

            description='A pre-trained Hugging Face model to classify audio',
            # (str) - a description for the interface;
            # if provided, appears above the input and output components.

            article=None,
            # (str) - an expanded article explaining the interface;
            # if provided, appears below the input and output components.
            # Accepts Markdown and HTML content.

            thumbnail=None,
            # (str) - path to image or src to use as display picture for models
            # listed in gradio.app/hub

            css=None,
            # (str) - custom css or path to custom css file
            # to use with interface.

            server_port=None,
            # (int) - will start gradio app on this port (if available)

            # server_name=networking.LOCALHOST_NAME,
            # (str) - to make app accessible on local network set to "0.0.0.0".

            height=500,
            width=900,

            allow_screenshot=True,
            # (bool) - if False, users will not see a button
            # to take a screenshot of the interface.

            allow_flagging=False,
            # (bool) - if False, users will not see a button
            # to flag an input and output.

            flagging_options=None,
            # (List[str]) - if not None, provides options a user must select
            # when flagging.

            encrypt=False,
            # (bool) - If True, flagged data will be encrypted
            # by key provided by creator at launch

            show_tips=False,
            # (bool) - if True, will occasionally show tips
            # about new Gradio features

            flagging_dir='flagged',
            # (str) - what to name the dir where flagged data is stored.

            analytics_enabled=True,

            enable_queue=False,
            # (bool) - if True, inference requests will be served through
            # a queue instead of with parallel threads.
            # Required for longer inference times (> 1min) to prevent timeout.
        )
