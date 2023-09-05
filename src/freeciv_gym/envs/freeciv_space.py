import numpy as np
from numpy.typing import NDArray
from gymnasium.spaces import Space
from typing import Any, Union, Optional, Sequence


class Onehot(Space):
    def __init__(
        self,
        shape: Sequence[int],
        dtype: type[np.integer[Any]] = np.int32,
        seed: Union[int, np.random.Generator, None] = None,
    ):
        assert dtype is not None
        self.type = np.dtype(dtype)

        for size in shape:
            assert isinstance(size, int) and size > 0
        Space.__init__(self, shape=shape, dtype=np.int64, seed=seed)

    @property
    def is_np_flattenable(self):
        return True

    @property
    def shape(self) -> tuple[int, ...]:
        return self.shape

    def sample(
        self, mask: Optional[Union[Sequence, NDArray]], dim: Union[int,Sequence[int]] = -1
    ) -> NDArray:
        raise NotImplementedError("To be implemented.")
