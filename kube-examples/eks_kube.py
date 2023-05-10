"""Execute a command."""

import sys
import os

import anyio
import boto3
import dagger


def get_aws_creds(profile: str = None):
    """Get AWS credentials using boto3"""
    if profile is None:
        profile = os.environ.get("AWS_PROFILE")
    else:
        raise ValueError(
            "Please set the arg `profile` or set the AWS_PROFILE environment variable."
        )

    if os.environ.get("AWS_ACCESS_KEY_ID") is None:
        print("Getting AWS credentials from boto")
        session = boto3.Session(profile_name=profile)
        credentials = session.get_credentials()

        os.environ["AWS_ACCESS_KEY_ID"] = credentials.access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
        os.environ["AWS_SESSION_TOKEN"] = credentials.token

    else:
        print(
            "Looks like we already have AWS creds set, skipping generation new credentials."
        )


async def test():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        if "AWS" not in os.environ:
            get_aws_creds()

        # configure the secrets for the build container
        aws_access_key_id = client.host().env_variable("AWS_ACCESS_KEY_ID").secret()
        aws_secret_access_key = (
            client.host().env_variable("AWS_SECRET_ACCESS_KEY").secret()
        )
        aws_session_token = client.host().env_variable("AWS_SESSION_TOKEN").secret()

        kube = (
            client.container()
            .from_("alpine/k8s:1.27.1")
            .pipeline(
                name="Kubectl Rollout Restart",
                description="Run a Kubectl rollout restart & wait for a successful restart",
            )
            .with_secret_variable("AWS_ACCESS_KEY_ID", aws_access_key_id)
            .with_secret_variable("AWS_SECRET_ACCESS_KEY", aws_secret_access_key)
            .with_secret_variable("AWS_SESSION_TOKEN", aws_session_token)
            .with_exec(
                [
                    "aws",
                    "eks",
                    "update-kubeconfig",
                    "--name=cluster-name",
                    "--region=us-east-1",
                    "--alias=cluster-name",
                ]
            )
            .with_exec(
                ["kubectl", "--context=cluster-name", "get", "pods", "-A"]
            )
        )

        output = await kube.stdout()

        print(output)


if __name__ == "__main__":
    anyio.run(test)
