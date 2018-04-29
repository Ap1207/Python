import boto3
import socket
import urllib.request
import paramiko
import datetime
#connect to AWS
ec2client = boto3.client('ec2')
#predeclared variables "main"
now = datetime.datetime.now()
domainn = 'domai_name_for_testing' # required for HTTP and SSH check
mainval= 'tag_from_AWS_Instance' # value for 'Server status check' section: Filter by 'tag-key'
owid = 'owner-id' # owner-id of AMIs
# cred for SSH
user = 'USEDRNAME'
port = 22
certname = 'pem_servificate_from_AWS.pem'
#other
print('===================')
print('Check: ' + domainn)
print('===================')
# check IP
try:
    ipadd=socket.gethostbyname(domainn)
    print('IP address:', ipadd)
except socket.gaierror:
    print('no IP address')
print('===================')
# check HTTP connection
print('HTTP connection check:')
gh_url = 'http://' + domainn
try:
    req = urllib.request.Request(gh_url)
    handler = urllib.request.urlopen(req, timeout=4)
    httpcode = handler.getcode()
    print("Code:", httpcode)

except urllib.error.URLError:
    print("Ups, Err Connection Timed Out")

except urllib.request.HTTPError as e:
    error_message = e.getcode()
    print("Error code:", error_message)
#SSH connect
print('===================')
print('SSH connection check:')
host = domainn
print("connecting...")
cert = paramiko.RSAKey.from_private_key_file(certname)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(hostname=host, username=user, pkey=cert, timeout=5)
    stdin, stdout, stderr = client.exec_command('ip addr')
    data = stdout.read() + stderr.read()
    print('Output:', data)
    client.close()
except socket.gaierror:
    print('unable to connect')
except socket.timeout:
    print('SSH timed out.')
print('===================')
print('Instances')
print('===================')
#Server status check
response = ec2client.describe_instances(
    Filters=[   #filter for private 'tag-key'
        {
            'Name': 'tag-key',
            'Values': [
                mainval,
            ]
        },
    ],
)

for i in range(len(response['Reservations'])):
    data = response['Reservations'][i]['Instances'][0]
    instid = data.get('InstanceId')
    print('InstanceId:', instid)
    imid = data.get('ImageId')
    statecode1 = data.get('State')
    statecode = statecode1.get('Name')
    print('State:', statecode)  # Instance status code
    print('-------------------')
    if statecode == 'stopped':
        stoppedinstance = response # remmember stopped instance details
        tinstance = instid # remmember stopped instance ID
        # Create an AMI of the stopped EC2 instance and add a descriptive tag based on the EC2 name along with the current date.

        desami = instid + '.' + now.isoformat() #A description for the new image.
        nbackup = 'backup_ami' + now.strftime("%H.%M") # A name for the new image.
        # check if instance status stopped. If stopped create backup
        conditionst = 'stopped'

        if statecode == conditionst:

            # Create AMI

            response2 = ec2client.create_image(
            Description=desami,
            #DryRun=True,
            InstanceId=tinstance,
            Name=nbackup,
            )

            print("AMI of Stopped Instance was created:")
            print("AMI name:", nbackup)
            print('-------------------')
            print("Stopped Instance shuld be terminated. It's ID:", tinstance)

            # Teminate Stopped instance and inform abut it
            response3 = ec2client.terminate_instances(
                InstanceIds=[
                    tinstance,
                ],
                #DryRun=True
            )

            print("Instance", tinstance, "terminated")
            print('-------------------')
    else:
        continue
print('===================')
print('AMIs')
print('===================')
# check all AMI
response4 = ec2client.describe_images(
    Filters=[
        {
            'Name': 'owner-id',
            'Values': [
                        owid,
                        ]
        }
]
)

for i in range(len(response4['Images'])):
    data = response4['Images'][i]
    amicd = data.get('CreationDate')
    amiimid = data.get('ImageId')
    print('ImageId:', amiimid)  # AMI ID
    print('CreationDate:', amicd) # AMI creation date

    amicd1 = amicd[0:10]  # change format in
    cd1 = now.isoformat()  # current date

    amicd2 = amicd1.replace("-", "/") # replace - to / in 'string' of AMI creation date

    cd2 = cd1[0:10].replace("-", "/") # display only date without time + replace - to / in 'string'

    amicd3 = datetime.datetime.strptime(amicd2, "%Y/%m/%d")
    cd3 = datetime.datetime.strptime(cd2, "%Y/%m/%d")

    amicd3plus = amicd3 + datetime.timedelta(days=7)

    if amicd3plus < cd3:

        # deregister outdated AMI
        response5 = ec2client.deregister_image(
            ImageId=amiimid,
            #DryRun=True
        )

        print("AMI with ID:", amiimid, "deleted")
        print('-------------------')
    else:
        print("Fresh AMI")
        print('-------------------')
