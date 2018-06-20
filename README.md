# Solution for interview in Dixons

This project is solution for interview question in dixons: http://tech.dixons.cz/devopstest

You can also read about it from here with flowchart: http://rovshanmusayev.blogspot.com/2018/06/dixonst-interview-question.html


## Getting Started


According to task definition here is how I have designed the solution:


Publisher will get input parameters from CI tool and will send data to general exchange and when consumer will run it will initiate n queue according to it's configuration (in our case it's two) and bind to the exchange. From that point data flow will be established. Consumer will call REST API of Monitoring tool for both queue and according to response it will remove message if it's successfully or requeue messages for defined iteration and period.


As as introduction let me tell you, it was developed and tested in Ubuntu 17.10. Publisher developed in bash, as a message queue was chosen RabbitMQ,  and consumer part developed in Python


# 1. Publisher

As a requirement  was publisher side should be as simple as possible, I have developed shell script which accept two parameters:

    Release number. It's mandatory parameter and cannot be empty
    Datetime. It can be empty, as in this case will be used current datetime by default

 The functionality of this script is only consist of adding devloyment message from CI tool to message queue. First it's declaring exchange and later adding deployment info to that exchange. If exchange already declared, as it can be declared also in the consumer part, then it will be skipped automatically. Meanwhile there is some validation of input parameters, checking resolution of commands, defining exit codes for external tools which will call that script.


PS... It's important to remember that if you don't want to loose messages consumer part should be started firstly, because of binding queue part will be done inside consumer. How it was designed currently during short period and of course it might be done better.
# 2. Queue

First I wanted to use REDIS. Actually it's in-memory and key-value database. It has not native features of Message queue, but it has some advantages like simplicity, size and speed. With RPOPLPUSH command in consumer it's very convenient to move one message (value) from one queue(key) to another and later after processing remove with LREM command. But it's not very reliable. What if consumer will stop working. Also speed is not an issue for us, because we will only ship little deployment information from time to time. Most important thing here our scenario with two consumer doesn't really works with Redis. 

So my second choose was RabbitMQ. It's open source, light-weight and nowadays very popular message broker system. It's using AMQP protocol for messaging and has support for python, which calls pika library.

In order to install RabbitMQ we need first install Docker and later  run

 

docker run -d --hostname localhost --name rabbitmq -p 15672:15672 -p 5672:5672 rabbitmq:3-management

 

It will pull docker image of Rabbit, run inside docker container and expose port to outside. It's important to say that there is no needed any configuration after installation and running. All that configuration will be done in the publisher and consumer part while running. 

Or we can use any cloud services which offers RabbitMQ.

# 3. Consumer 

Most important part is the consumer part. I have developed python application which will consume this queue. Virtuanev and pip tool were used to setting environment and Pika library for interracting with RabbitMQ.

It's multi-thread and configurable. So it will read general and queue specific parameters from config file and will run every queue processing on separate thread. It's useful because of, the queues will not wait each other while consumer process and will work independently. On every thread application will declare common exchange, separate queues and bind these queues to that exchange. After binding process the messages which sent to exchange by publisher will be replicated to all queues. Queues will process these messages in it's own thread and send REST request to defined API in config file with the defined body and URL. If response is positive the message will be removed from queue. Positive response means that - http codes which is listed in config file. 

If response is negative then it will send messages to Retry queue. After defined time the message will return back to main queue and it will attempt again. This process will be repeated till if all (defiined) attempts failed. Finally the failed  message will be marked as dead and will send to Dead queue. This Dead queue is persistent and might be processed later on.



### Prerequisites


```OS: Ubuntu 17.10. Another prerequisites will be installed by installation script```


### Installation

Run the following command in order to have consumer up and running:

```
./install_run.sh
```

## Authors

* **Rovshan Musayev** 



