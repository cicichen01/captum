#!/usr/bin/env python3
import numpy as np
import torch

import captum.optim._core.loss as opt_loss
from captum.optim._utils.models import collect_activations
from tests.helpers.basic import BaseTest, assertArraysAlmostEqual
from tests.helpers.basic_models import BasicModel_ConvNet_Optim

CHANNEL_ACTIVATION_0_LOSS = 1.3
CHANNEL_ACTIVATION_1_LOSS = 1.3


def get_loss_value(model, loss, input_shape=[1, 3, 1, 1]):
    module_outputs = collect_activations(model, loss.target, torch.ones(*input_shape))
    loss_value = loss(module_outputs)
    try:
        return loss_value.item()
    except ValueError:
        return loss_value.detach().numpy()


class TestDeepDream(BaseTest):
    def test_channel_deepdream(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.DeepDream(model.layer)
        assertArraysAlmostEqual(
            get_loss_value(model, loss),
            [[[CHANNEL_ACTIVATION_0_LOSS ** 2]], [[CHANNEL_ACTIVATION_1_LOSS ** 2]]],
        )


class TestChannelActivation(BaseTest):
    def test_channel_activation_0(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ChannelActivation(model.layer, 0)
        self.assertAlmostEqual(get_loss_value(model, loss), CHANNEL_ACTIVATION_0_LOSS)

    def test_channel_activation_1(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ChannelActivation(model.layer, 1)
        self.assertAlmostEqual(get_loss_value(model, loss), CHANNEL_ACTIVATION_1_LOSS)


class TestNeuronActivation(BaseTest):
    def test_neuron_activation_0(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.NeuronActivation(model.layer, 0)
        self.assertAlmostEqual(get_loss_value(model, loss), CHANNEL_ACTIVATION_0_LOSS)


class TestTotalVariation(BaseTest):
    def test_total_variation(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.TotalVariation(model.layer)
        self.assertAlmostEqual(get_loss_value(model, loss), 0.0)


class TestL1(BaseTest):
    def test_l1(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.L1(model.layer)
        self.assertAlmostEqual(
            get_loss_value(model, loss),
            CHANNEL_ACTIVATION_0_LOSS + CHANNEL_ACTIVATION_1_LOSS,
            places=6,
        )


class TestL2(BaseTest):
    def test_l2(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.L2(model.layer)
        self.assertAlmostEqual(
            get_loss_value(model, loss),
            (CHANNEL_ACTIVATION_0_LOSS ** 2 + CHANNEL_ACTIVATION_1_LOSS ** 2) ** 0.5,
            places=5,
        )


class TestDiversity(BaseTest):
    def test_diversity(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.Diversity(model.layer)
        self.assertAlmostEqual(
            get_loss_value(model, loss, input_shape=[2, 3, 1, 1]),
            -1,
        )


class TestActivationInterpolation(BaseTest):
    def test_activation_interpolation_0_1(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ActivationInterpolation(
            target1=model.layer,
            channel_index1=0,
            target2=model.layer,
            channel_index2=1,
        )
        self.assertAlmostEqual(
            get_loss_value(model, loss, input_shape=[2, 3, 1, 1]),
            CHANNEL_ACTIVATION_0_LOSS + CHANNEL_ACTIVATION_1_LOSS,
            places=6,
        )


class TestAlignment(BaseTest):
    def test_alignment(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.Alignment(model.layer)
        self.assertAlmostEqual(
            get_loss_value(model, loss, input_shape=[2, 3, 1, 1]), 0.0
        )


class TestNeuronDirection(BaseTest):
    def test_neuron_direction(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.NeuronDirection(model.layer, vec=torch.ones(1, 1, 1, 1))
        a = 1
        b = [CHANNEL_ACTIVATION_0_LOSS, CHANNEL_ACTIVATION_1_LOSS]
        cos_sim = np.inner(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        cos_sim = np.sum(cos_sim)
        self.assertAlmostEqual(get_loss_value(model, loss), cos_sim, places=6)


class TestTensorDirection(BaseTest):
    def test_tensor_direction(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.TensorDirection(model.layer, vec=torch.ones(1, 1, 1, 1))
        a = 1
        b = [CHANNEL_ACTIVATION_0_LOSS, CHANNEL_ACTIVATION_1_LOSS]
        cos_sim = np.inner(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        cos_sim = np.sum(cos_sim)
        self.assertAlmostEqual(get_loss_value(model, loss), cos_sim, places=6)


class TestActivationWeights(BaseTest):
    def test_activation_weights_0(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ActivationWeights(model.layer, weights=torch.zeros(1))
        assertArraysAlmostEqual(get_loss_value(model, loss), np.zeros((1, 2, 1)))

    def test_activation_weights_1(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ActivationWeights(
            model.layer, weights=torch.ones(1), neuron=True
        )
        assertArraysAlmostEqual(
            get_loss_value(model, loss),
            [CHANNEL_ACTIVATION_0_LOSS, CHANNEL_ACTIVATION_1_LOSS],
        )


class TestCompositeLoss(BaseTest):
    def test_negative(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = -opt_loss.ChannelActivation(model.layer, 0)
        self.assertAlmostEqual(get_loss_value(model, loss), -CHANNEL_ACTIVATION_0_LOSS)

    def test_addition(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = (
            opt_loss.ChannelActivation(model.layer, 0)
            + opt_loss.ChannelActivation(model.layer, 1)
            + 1
        )
        self.assertAlmostEqual(
            get_loss_value(model, loss),
            CHANNEL_ACTIVATION_0_LOSS + CHANNEL_ACTIVATION_1_LOSS + 1,
            places=6,
        )

    def test_subtraction(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = (
            opt_loss.ChannelActivation(model.layer, 0)
            - opt_loss.ChannelActivation(model.layer, 1)
            - 1
        )
        self.assertAlmostEqual(
            get_loss_value(model, loss),
            CHANNEL_ACTIVATION_0_LOSS - CHANNEL_ACTIVATION_1_LOSS - 1,
        )

    def test_multiplication(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ChannelActivation(model.layer, 0) * 10
        self.assertAlmostEqual(
            get_loss_value(model, loss), CHANNEL_ACTIVATION_0_LOSS * 10
        )

    def test_multiplication_error(self) -> None:
        model = BasicModel_ConvNet_Optim()
        with self.assertRaises(TypeError):
            opt_loss.ChannelActivation(model.layer, 0) * "string"
        with self.assertRaises(TypeError):
            opt_loss.ChannelActivation(model.layer, 0) * opt_loss.ChannelActivation(
                model.layer, 1
            )

    def test_division(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ChannelActivation(model.layer, 0) / 10
        self.assertAlmostEqual(
            get_loss_value(model, loss), CHANNEL_ACTIVATION_0_LOSS / 10
        )

    def test_division_error(self) -> None:
        model = BasicModel_ConvNet_Optim()
        with self.assertRaises(TypeError):
            opt_loss.ChannelActivation(model.layer, 0) / "string"
        with self.assertRaises(TypeError):
            opt_loss.ChannelActivation(model.layer, 0) / opt_loss.ChannelActivation(
                model.layer, 1
            )

    def test_pow(self) -> None:
        model = BasicModel_ConvNet_Optim()
        loss = opt_loss.ChannelActivation(model.layer, 0) ** 2
        self.assertAlmostEqual(
            get_loss_value(model, loss),
            CHANNEL_ACTIVATION_0_LOSS ** 2,
            places=6,
        )

    def test_pow_error(self) -> None:
        model = BasicModel_ConvNet_Optim()
        with self.assertRaises(TypeError):
            opt_loss.ChannelActivation(model.layer, 0) ** "string"
        with self.assertRaises(TypeError):
            opt_loss.ChannelActivation(model.layer, 0) ** opt_loss.ChannelActivation(
                model.layer, 1
            )
