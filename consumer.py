import threading, datetime, time, os, sys, pika, requests, configparser, logging


class myThread (threading.Thread):
    
    def __init__(self, queue, exchange, config_data):
        threading.Thread.__init__(self)
        self.queue = queue
        self.exchange = exchange
        self.config_data = config_data
        logging.info("Initializing connection for "+self.queue)
        self.connection = pika.BlockingConnection(params) # Connect to CloudAMQP
        self.channel = self.connection.channel() # start a channel
        self.channel.confirm_delivery()
        #self.channel = connection.channel() # start a channel
        logging.info("Declaring exchange "+self.exchange) 
        self.channel.exchange_declare(exchange=self.exchange, durable=True, exchange_type='fanout') # declare exchange name

        self.retry_exchange=self.exchange+".retry" # generating retry exchange name
        logging.info("Declaring retry exchange "+self.retry_exchange) 
        self.channel.exchange_declare(exchange=self.retry_exchange, durable=True, exchange_type='direct') # declare retry exchange name

    
    def run(self):
        
        self.retry_queue=self.queue+".retry" # generating retry queue name
        
        # normal queue
        result = self.channel.queue_declare(queue=self.queue,exclusive=False, durable=True, arguments={
#                          'x-message-ttl' : 10000,
                          'x-dead-letter-exchange' : self.retry_exchange,
                          "x-dead-letter-routing-key" : self.retry_queue, # if not specified, queue's routing-key is used
        }) # declare queue
        self.channel.queue_bind(exchange=self.exchange,queue=self.queue) #bind queue to exchange
        logging.info(self.queue+" was declared and binded to exchange "+self.exchange)
        
        # retry queue
        result = self.channel.queue_declare(queue=self.retry_queue, exclusive=False, durable=True, arguments={
                          'x-message-ttl' : 10000,
                          'x-dead-letter-exchange' : self.retry_exchange,
                          "x-dead-letter-routing-key" : self.queue, # if not specified, queue's routing-key is used
        }) # declare queue
        self.channel.queue_bind(exchange=self.retry_exchange,queue=self.queue) #bind queue to exchange
        self.channel.queue_bind(exchange=self.retry_exchange,queue=self.retry_queue) #bind retry queue to retry exchange
        logging.info(self.retry_queue+" was declared and binded to exchange "+self.retry_exchange)
        
        # starting to consume
        self.channel.basic_consume(lambda ch, method, properties, 
            body: callback_with_extended_args(ch, method, properties, body, self.queue, self.config_data),
            queue=self.queue,
            no_ack=False)
        
        try:
        	self.channel.start_consuming() 
        except KeyboardInterrupt:
	        self.channel.stop_consuming();

        self.connection.close()


#Callback function for recurtion
def callback_with_extended_args(ch, method, properties, body, queue, config_data):
    
    #Logic for parsing and generating body specific for the config
    send_request(ch, method, properties, body, queue, config_data)

def send_request(ch, method, properties, body, queue, config_data):
    if config_data['API_METHOD'] == "POST":
        r = requests.post(config_data['API_URL'], data=config_data['API_DATA'])
    elif config_data['API_METHOD'] == "PUT":
        r = requests.put(config_data['API_URL'], data=config_data['API_DATA'])
    
    if str(r.status_code) in config_data['SUCCESS_CODES']:
        logging.info(str(body)+" consumed in "+queue)
        ch.basic_ack(delivery_tag = method.delivery_tag)
    else:
        if properties.headers == None or 'x-death' not in properties.headers or properties.headers['x-death'][0]['count'] < 3:
            ch.basic_reject(delivery_tag = method.delivery_tag, requeue=False)
            logging.warning(str(r.status_code) + " - " + str(body)+ " moved to Retry letter queue")
        else:
            ch.basic_ack(delivery_tag = method.delivery_tag)
            logging.error(str(r.status_code) + " - " + str(body)+ " moved to Dead letter queue")

    time.sleep(1) # delays for 5 seconds
    return;


                    
#reading config
print("Reading configuration file config.ini ...")
config = configparser.ConfigParser() #loading library
config.read('config.ini') # loading config file
exchange=config['DEFAULT']['EXCHANGE'] # reading exchange name from config file
log_level=config['DEFAULT']['LOG_LEVEL'] # reading log level from config file
cloudamqp_url=config['DEFAULT']['CLOUDAMQP_URL'] # reading CLOUD from config file

#Setting logging from configuration
print("Log level is "+log_level)

exec("log_level=logging."+log_level)

logging.basicConfig(level=log_level,
                    format='[%(threadName)-10s] %(asctime)s %(levelname)s %(message)s',
                    )

# Parsing CLOUDAMQP_URL
url = os.environ.get('CLOUDAMQP_URL', cloudamqp_url)
params = pika.URLParameters(url)
params.socket_timeout = 5

#logging.info("Initializing connection for "+self.queue)
#connection = pika.BlockingConnection(params) # Connect to CloudAMQP

# Looping queues from config and creating seperate threads
# For all section of queue will be opened new connection to RabbitMQ database
# Connection will be initilized once only in the beginning
for section in  config.sections():
    
    # Reading config from each section
    queue=config[section]['QUEUE']
    config_data=config[section]

    # Create new threads
    logging.info("Creating thread for "+queue)
    thread = myThread(queue, exchange, config_data)
    thread.start()

    