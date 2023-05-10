"""Run tests for a single Python version."""

import sys
import anyio
import dagger
import os

async def docker_image_build():
  async with dagger.Connection(dagger.Config(log_output=sys.stdout)) as client:
    src = client.host().directory(".")

    image = (
        client.container()
        .pipeline(name='Builder', description='Build the image')
        .build(
            context = src,
            dockerfile = "Dockerfile",
            build_args=[
                dagger.BuildArg("HELLO", os.environ.get("HELLO", "hey mom!"))
            ]
        )
    )
    
    await image.publish("ttl.sh/test_image:1h")


if __name__ == "__main__":
  anyio.run(docker_image_build)