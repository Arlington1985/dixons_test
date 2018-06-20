#!/bin/bash
#Developed for Dixons Devops position by Rovshan

#Constants
exchange="deployment"
#RABBIT_CLI="python rabbitmqadmin.py -U amqp://kfwbzgri:JLBKF69CjWq-c1H3UAShM0utYFvrPyMs@duckbill.rmq.cloudamqp.com -V kfwbzgri -P 443 --ssl"  
RABBIT_CLI="python rabbitmqadmin.py -U amqp://guest:guest@localhost"  

#Input parameters
release_no=$1 #Deployment release number
release_dt=$2 #Deployment release datetime


#Sub functions

#Generate unique id for trackig process thread in the logs
uuid=$(uuidgen)

#Generate current time
now() {
   echo `date '+%Y-%m-%d %H:%M:%S'`
}


#Declaring exchange for sending sending information to
declare_exchange() {
    $RABBIT_CLI declare exchange name=$exchange durable=true type=fanout
}

#Adding information to 
publish_message() {
	$RABBIT_CLI publish exchange=$exchange routing_key="" payload="$msg_json"
	
	#python rabbitmqadmin.py -U amqp://guest:guest@localhost publish exchange=deployment routing_key="" payload="$msg_json"
	#echo "$RABBIT_CLI $CMD_PUBLISH"
}

#Main 

echo ""
echo "[`now`] [$uuid] [INFO]    Process started"
echo "[`now`] [$uuid] [INFO]    Script input parameters: release_number=\"$release_no\", release_datetime=\"$release_dt\""
wrong_input=0
if [ -z "$release_no" ]
then
	echo "[`now`] [$uuid] [ERROR]   Deployment release number cannot be null"
	wrong_input=1
	exit_code=1
else
	if [ -z "$release_dt" ]
	then
		release_dt=`now` #if not set, assign default value current datetime
		echo "[`now`] [$uuid] [WARNING] Deployment release datetime was not set, assigning current datetime by default"	
		wrong_input=1
	fi 
	if [ $wrong_input = 1 ]
	then
		echo "[`now`] [$uuid] [INFO]    Revised input parameters: release_number=$release_no, release_datetime=$release_dt"
	fi

	msg_json="{\"release_number\":\"$release_no\",\"datetime\":\"$release_dt\"}"
	echo "[`now`] [$uuid] [INFO]    Generated JSON from parameters: $msg_json"

	output=`declare_exchange`
	if [ $? = 0 ]
	then
		echo "[`now`] [$uuid] [INFO]    $output"
		output=`publish_message`
		if [ $? = 0 ]
		then
			echo "[`now`] [$uuid] [INFO]    $output"
		else
			echo "[`now`] [$uuid] [ERROR]   $output"
			echo "[`now`] [$uuid] [ERROR]   Error while publishing"
			exit_code=1
		fi
	else
		echo "[`now`] [$uuid] [ERROR]   $output"
		echo "[`now`] [$uuid] [ERROR]   Error while declaring exchange"
		exit_code=1
	fi
fi
echo "[`now`] [$uuid] [INFO]    Process ended"
echo ""

#Finally exiting with defined exit code in order 
#for external tools to be able detect process was
#finished properly or not
exit $exit_code 
