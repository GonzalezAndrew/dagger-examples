import anyio
import dagger

'''
How to use a local image for dagger. Stolen from https://github.com/dagger/dagger/issues/5235


$ docker build -t my-local-image - <<EOF
FROM alpine
ENV HELLO=Docker
EOF
'''

IMAGE_NAME = "my-local-image"


async def main():
    async with dagger.Connection() as client:
        var = await (
            client.container()
            .with_(docker_image(
                IMAGE_NAME,
                client.host().unix_socket("/var/run/docker.sock"),
            ))
            .env_variable("HELLO")
        )

    print(f"Hello from {var}!")


def docker_image(name: str, socket: dagger.Socket):
    """Import a docker image into container."""

    def _docker_image(ctr: dagger.Container):
        return ctr.import_(
            ctr.with_(
                docker_exec(
                    ["image", "save", "-o", "image.tar", name],
                    socket,
                )
            )
            .file("image.tar")
        )
    return _docker_image


def docker_exec(args: list[str], socket: dagger.Socket):
    """Execute a docker command."""

    def _docker_exec(ctr: dagger.Container):
        return (
            ctr.from_("docker:23.0.1-cli")
            .with_unix_socket("/var/run/docker.sock", socket)
            .with_exec(args)
        )
    return _docker_exec


anyio.run(main)