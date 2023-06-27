from unittest import TestCase

import pandas as pd
import pytest
import torch
from gpytorch.kernels import PeriodicKernel, ScaleKernel
from gpytorch.means import ConstantMean

from xopt.generators.bayesian.expected_improvement import ExpectedImprovementGenerator
from xopt.generators.bayesian.models.standard import StandardModelConstructor
from xopt.vocs import VOCS


class TestCustomConstructor(TestCase):
    def test_uniform_model_generation(self):
        my_vocs = VOCS(
            variables={"x": [0, 1]},
            objectives={"y": "MAXIMIZE"},
            constraints={"c": ["LESS_THAN", 0]},
        )

        # specify a periodic kernel for each output (objectives and constraints)
        covar_module = {
            "y": ScaleKernel(PeriodicKernel()),
            "c": ScaleKernel(PeriodicKernel()),
        }

        model_constructor = StandardModelConstructor(covar_modules=covar_module)
        generator = ExpectedImprovementGenerator(
            vocs=my_vocs, model_constructor=model_constructor
        )

        # define training data to pass to the generator
        train_x = torch.tensor((0.2, 0.5, 0.6))
        train_y = 5.0 * torch.cos(2 * 3.14 * train_x + 0.25)
        train_c = 2.0 * torch.sin(2 * 3.14 * train_x + 0.25)

        training_data = pd.DataFrame(
            {"x": train_x.numpy(), "y": train_y.numpy(), "c": train_c}
        )

        generator.add_data(training_data)
        generator.train_model()

    def test_nonuniform_model_generation(self):
        my_vocs = VOCS(
            variables={"x": [0, 1]},
            objectives={"y": "MAXIMIZE"},
            constraints={"c": ["LESS_THAN", 0]},
        )

        # specify a periodic kernel for each output (objectives and constraints)
        covar_module = {"y1": ScaleKernel(PeriodicKernel())}

        model_constructor = StandardModelConstructor(covar_modules=covar_module)
        generator = ExpectedImprovementGenerator(
            vocs=my_vocs, model_constructor=model_constructor
        )

        # define training data to pass to the generator
        train_x = torch.tensor((0.2, 0.5, 0.6))
        train_y = 5.0 * torch.cos(2 * 3.14 * train_x + 0.25)
        train_c = 2.0 * torch.sin(2 * 3.14 * train_x + 0.25)

        training_data = pd.DataFrame(
            {"x": train_x.numpy(), "y": train_y.numpy(), "c": train_c}
        )

        generator.add_data(training_data)
        generator.train_model()

    def test_prior_mean(self):
        my_vocs = VOCS(
            variables={"x": [0, 1]},
            objectives={"y": "MAXIMIZE"},
            constraints={"c": ["LESS_THAN", 0]},
        )

        class ConstraintPrior(torch.nn.Module):
            def forward(self, X):
                return X.squeeze(dim=-1) ** 2

        model_constructor = StandardModelConstructor(
            mean_modules={"c": ConstraintPrior()}
        )
        generator = ExpectedImprovementGenerator(
            vocs=my_vocs, model_constructor=model_constructor
        )

        # define training data to pass to the generator
        train_x = torch.tensor((0.2, 0.5))
        train_y = 1.0 * torch.cos(2 * 3.14 * train_x + 0.25)
        train_c = train_x**2

        training_data = pd.DataFrame(
            {"x": train_x.numpy(), "y": train_y.numpy(), "c": train_c}
        )

        generator.add_data(training_data)
        generator.train_model()

    def test_trainable_prior_mean(self):
        my_vocs = VOCS(
            variables={"x": [0, 1]},
            objectives={"y": "MAXIMIZE"},
        )

        # test bad trainable_mean_keys
        with pytest.raises(ValueError):
            StandardModelConstructor(
                mean_modules={"y": ConstantMean()},
                trainable_mean_keys=["f"],
            )

        for trainable in [True, False]:
            if trainable:
                trainable_mean_keys = ["y"]
            else:
                trainable_mean_keys = []
            model_constructor = StandardModelConstructor(
                mean_modules={"y": ConstantMean()},
                trainable_mean_keys=trainable_mean_keys,
            )
            generator = ExpectedImprovementGenerator(
                vocs=my_vocs, model_constructor=model_constructor
            )

            # define training data to pass to the generator
            train_x = torch.tensor((0.2, 0.5))
            train_y = 1.0 * torch.cos(2 * 3.14 * train_x + 0.25)

            training_data = pd.DataFrame({"x": train_x.numpy(), "y": train_y.numpy()})

            generator.add_data(training_data)
            model = generator.train_model()

            # check for trainable parameters
            trainable_params_exist = False
            for param in model.models[0].mean_module.parameters():
                if param.requires_grad:
                    trainable_params_exist = True
            assert trainable_params_exist == trainable
