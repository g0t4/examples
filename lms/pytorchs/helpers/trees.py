from torch import nn
import numpy as np
# ***  use print from rich with ipython repl, so so pretty!!
from rich import print

# FYI! a tree is easier for me to visualize when it comes to > 3 dimensions, and even with 3D too when it comes to calculations


def print_tree(tensor, nesting=0):
    padding = "   " * nesting
    for i in range(0, tensor.shape[0]):
        remain = tensor[i]
        if remain.shape == ():
            print(padding, remain)
        else:
            print(padding, i)
            print_tree(remain, nesting + 1)


def print_treearrays(tensor, nesting=0):
    # compact format for innermost dimension

    padding = "   " * nesting
    if len(tensor.shape) < 2:
        # print 1D arrays as an array (compact)
        #  also that final dimension is a critical one to understand the shape of the data!
        print(padding, tensor)
        return

    for i in range(0, tensor.shape[0]):
        remain = tensor[i]
        if remain.shape == ():
            print(padding, remain)
        else:
            print(padding, i)
            print_treearrays(remain, nesting + 1)


def print_linear(linear, actual_inputs=None):
    outputs = linear.out_features
    inputs = linear.in_features
    for i in range(outputs):
        output_weights = linear.weight[i]
        bias = linear.bias[i]
        calcs = []
        for j in range(inputs):
            weight = output_weights[j]
            weight_value = weight.detach().numpy()

            # ensure 4 decimals (not truncated)
            value_rounded = f"{np.round(weight_value, 4):.4f}"

            if actual_inputs is None:
                value = f"{value_rounded} * i{j}"
            else:
                # FYI its ok to use truncated decimals b/c the value is the same across all rows (outputs)
                #  so if I add rounding of actual_input_value, use truncated display (not 0 padded decimal places)
                actual_input_value = actual_inputs[j].detach().numpy()
                value = f"{value_rounded} * {actual_input_value}"

            if j == 0:
                # add leading space before first value (so all values align in columns)
                if weight_value < 0:
                    # "-1" is the goal here (since its the leading number for the formula)
                    value = f"{value}"
                else:
                    # " 1" is the goal here (since its the leading number for the formula)
                    value = f" {value}"
            else:
                if weight_value < 0:
                    value = f" {value}"  # if - sign then dont show +?
                    # add space after -
                    value = value.replace("-", "- ")
                else:
                    value = f" + {value}"
            calcs.append(value)

        bias_value = bias.detach().numpy()
        bias_rounded = f"{np.round(bias_value, 4):.4f}"
        if bias < 0:
            bias_rounded = bias_rounded.replace("-", "- ")
            calcs.append(f" {bias_rounded}")
        else:
            calcs.append(f" + {bias_rounded}")
        output_string = "".join(calcs)
        print(f"o{i} = {output_string}")


def print_wes(what):
    if isinstance(what, nn.Linear):
        print_linear(what)
    else:
        print_treearrays(what)


def print_label(label, what):
    print("[bold red]" + label + ":")
    print_wes(what)
