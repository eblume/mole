import boto3

# TODO this should eventually literally import the blumoops module, but we're a ways off from that

boto_session = boto3.Session(profile_name="blumeops")
