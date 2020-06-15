#!/usr/bin/env python3

# ---------------------------------------------------------------------------- #
#                                                                              #
# CATHODE ~ Putting (A)NODEs to work                                           #
#          (for financial time-series prediction and simulation)               #
#                                                                              #
# |> Datasets/Data-loading convenience functions <|                            #
#                                                                              #
# (C) 2020-* Emanuele Ballarin <emanuele@ballarin.cc>                          #
# (C) 2020-* Arianna Tasciotti                                                 #
# (C) 2020-* Milton Nicolas Plasencia Palacios                                 #
#                                                                              #
# Distribution: Apache License 2.0                                             #
#                                                                              #
# Eventually-updated version: https://github.com/emaballarin/cathode           #
# Restricted-access material: https://bit.ly/cathode-sml-reserved              #
#                                                                              #
# ---------------------------------------------------------------------------- #


# ------- #
# IMPORTS #
# ------- #

import numpy  # Just force the right OpenMP implementation!

import vaex  # Dataframe provider
import vaex as vx

import matplotlib.pyplot as plt  # Basic plotting

# Self-rolled utilities
from src.util.datamanip import data_by_tick
from src.util.datamanip import data_by_tick_col

# Neural Networks / Neural ODEs
import torch as th
from torch.utils.data import Dataset


# --------- #
# FUNCTIONS #
# --------- #


# DESC
# XYZ


# ------- #
# CLASSES #
# ------- #


# PyTorch dataset scaffold for QUANDL-like stock data (HDF5)
class StockDataset(Dataset):
    def __init__(
        self,
        hdf5_file,
        company,
        col_n,
        split_ratio,
        window_size,
        sliding_step=1,
        normalize=True,
        train=True,
    ):
        self.dataframe = vx.open(hdf5_file)
        self.split_ratio = split_ratio
        self.window_size = window_size
        self.sliding_step = sliding_step
        self.train = train

        if isinstance(col_n, tuple):
            col_n = tuple(["date"]) + col_n
        else:
            col_n = tuple(["date"]) + tuple([col_n])

        self.data = data_by_tick_col(self.dataframe, company, col_n)

        if normalize:
            for col in col_n:
                if col != "date":
                    self.data[col] = (
                        self.data[col] - self.data[col].mean()
                    ) / self.data[col].std()

        self.data = (self.data).values

        if train:
            self.data = self.data[: int(len(self.data) * self.split_ratio)]

    def __len__(self):
        if self.train:
            return (
                len(self.data) - self.window_size + 2 - self.sliding_step
            )  # number of windows
        else:
            return 1000

    def __getitem__(self, idx: int):
        if self.train:
            window = self.data[
                self.sliding_step * idx : (self.sliding_step * idx) + self.window_size
            ]
        else:
            window = self.data
        input_window, output_window = (
            window[: int(len(window) * self.split_ratio)],
            window[int(len(window) * self.split_ratio) :],
        )
        out_dict = {"past": input_window, "future": output_window}
        return out_dict