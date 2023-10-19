# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


# def DIVIDE(n, d):
# * DIVIDE() divides and rounds down, rather than just divides and
# *rounds toward 0.  It is assumed that the divisor is positive."""
# return parseInt( (n) / (d) - (( (n) < 0 && (n) % (d) < 0 ) ? 1 : 0) )
import numpy as np


def FC_WRAP(value, arange):
    # return (value % (arange) + (arange) if (value) % (arange) != 0 else 0) \
    return ((value + arange) % arange if value % arange != 0 else 0) \
        if value < 0 else (value % arange if value >= arange else value)


def XOR(a, b):
    return (a or b) and not (a and b)


def byte_to_bit_array(abyte_array, size=None):
    bit_array = []
    for abyte in abyte_array:
        bit_array.extend([int(x) for x in "{0:0>8}".format(bin(abyte)[2:])][::-1])
    return bit_array[:size]


def find_set_bits(bit_vector):
    set_bits = []
    index = bit_vector.next_set_bit(0)

    while index != -1:
        set_bits.append(index)
        index = bit_vector.next_set_bit(index + 1)

    return set_bits


def sign(x):
    return (x > 0) - (x < 0)


def format_hex(num):
    hex_value = hex(num)[2:]
    formatted_hex = format(int(hex_value, 16), '02X')
    return formatted_hex


def read_sub_arr_with_wrap(arr, start_x, end_x, start_y, end_y):
    """ consider map_const.TF_WRAPX == 1 """
    if len(arr.shape) == 2:
        (length, width) = arr.shape
    else:
        (length, width, height) = arr.shape

    if start_y < 0:
        start_y = 0
    if end_y > width:
        end_y = width

    if start_x < 0 or end_x > length:
        if start_x < 0:
            start_x = length + start_x
        else:
            end_x = end_x % length

        if len(arr.shape) == 2:
            arr_1 = arr[start_x:, start_y: end_y]
            arr_2 = arr[:end_x, start_y: end_y]
        else:
            arr_1 = arr[start_x:, start_y: end_y, :]
            arr_2 = arr[:end_x, start_y: end_y, :]
        return np.concatenate((arr_1, arr_2), axis=0)

    else:
        if len(arr.shape) == 2:
            return arr[start_x: end_x, start_y: end_y]
        else:
            return arr[start_x: end_x, start_y: end_y, :]



def geometric_sequence(length: int, start: int, end: int):
    start_end = np.log(np.array([start + 1e-4, end + 1e-4]))
    log_array = np.linspace(*start_end, length)
    return np.exp(log_array).astype(int).tolist()
