import tensorflow_datasets as tfds

# This will download + prepare CIFAR-10 to ~/.tensorflow_datasets the first time
(ds_train, ds_test), ds_info = tfds.load(
    "cifar10",
    split=["train", "test"],
    as_supervised=True,   # returns (image, label)
    with_info=True,
)
