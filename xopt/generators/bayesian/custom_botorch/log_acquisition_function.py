import torch
from botorch.acquisition import AcquisitionFunction
from botorch.utils import t_batch_mode_transform
from torch import Tensor
from torch.nn import Module
from torch.nn.functional import softplus


class LogAcquisitionFunction(AcquisitionFunction):
    def __init__(
        self,
        acq_function: AcquisitionFunction,
    ) -> None:
        Module.__init__(self)
        self.acq_func = acq_function

    @t_batch_mode_transform(expected_q=1, assert_output_shape=False)
    def forward(self, X: Tensor) -> Tensor:
        # apply a softplus transform to avoid numerical gradient issues
        return torch.log(softplus(self.acq_func(X), 20))
