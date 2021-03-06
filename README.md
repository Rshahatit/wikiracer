# Wikiracer 

## High Level Architecture 
### Diagram
![Image of diagram](https://user-images.githubusercontent.com/11155241/79872394-966ab800-839a-11ea-8011-41cd8c68fa53.png)

## What the code does:
The wikiracer code takes in a source or destination which can be a wikipedia url or a title for a wikipedia page. It starts at the source page and calls the media wiki api to find the wikipedia pages that have links on that page. It continues calling the media wiki api - searching for the destination page - among the links on the upcoming pages. While it is requesting links on pages from the media wiki api it is asynchronously checking if any of the links it already has retrieved has the destination page among them. I use two asynchronous queues to give each kind of worker their jobs. One queue (titles to visit) is giving our search worker a title and a set of links on the page --- that worker checks if the destination page is in that set then adds all the links into a queue for the fetch worker to fetch all the links for those pages. When the fetch worker gets the links for the title it puts them in the queue (titles to visit) for the search worker to keep checking. I keep track of the depth by incrementing it each time the titles previous page changes. So whenever the previous changes the depth will change because that means we are checking a new depth. I chose to stop searching after a depth of 15 and return to the user that a path could not be found up to that depth. I wrote a test for it but I have commented it out because it takes a long time.

The code optimizes for the wall clock time of jumping from page to page like the instructions specifies. I chose to do this asynchronously because of the nature of how many IO operations occur and the time that is wasted waiting for that request. Doing it asynchronously allows me to only worry about one thread, the event loop will take care of running the workers whenever there is free time from a request. 
I also have a Dockerfile included with my application. You can utilize it through the make file, I give instructions below. I realized in order to test you will need python 3.7 because of asyncio's new run method. I have provided a docker compose file so the tests will run in a docker container. 

## Instructions for how to run your Wikiracer:
#### Testing:
```Shell 
make test
```
This command installs the requirements from the requirements.txt file and runs the automated tests end to end tests in django in a docker container using the docker compose file.

#### Spin up docker container with application running:
 ```Shell
 make run
 ```
Runs the docker container that will be listening on *localhost:8000* through the docker compose file.

#### You can send a post request with a (filling in source and dest with a wiki url or page title)
```Shell 
curl -X POST http://127.0.0.1:8000/findpath/  -H 'Content-Type: application/json' -d '{"source" : "Mickey Mouse","destination" : "Albert Einstein"}’
```

#### Other make commands available:
 ```Shell
 make build
 make run
 ```
 
## Strategies I tried:
Initial thoughts:
At first I thought I could have a database to store everything. That would take care of the async issues and they ensure the destination page hasn't been found by checking the db before making any other calls. I thought making those db calls would be unnecessary and time consuming so I pushed forward without pursuing that approach.

### node js

I have been going through this book called *Building Enterprise Javascript Applications*, I thought to start attempting this with node. The asynchronous nature of nodejs made it attractive for decreasing wall clock time between pages. I had a boilerplate app ready to go from the book. I started thinking about how to solve the problem of wikiracing. 
I started with the Media wiki api. I read through some of the documentation to find how we can get all the links from a wikipedia page given its title. After finding what I was looking for I poked around more to see if anything else could be useful, I found an api call that can give you all the pages that link to a given page. 
A big concept in the book was test driven development, I find it really hard to do without fully understanding how to solve the problem, but I did know what the problem had to do so I wrote an end to end test using cucumber and gherkin to find a path between Rami Malek and 12 Strong (The pages could be easily changed in the test) I chose 12 strong because it just one page away from Rami Malek after 2018 in Film. 
I wrote the test to make a request to */findpath* with a payload of a source and destination. Then the response should be json with the path. (I wasn’t too focused on returning the time just yet). I started with a findpath handler function to accept the request. This handler would start the process to begin searching for the destination.
Now for the algorithm,  I thought of three different algorithms to attempt to implement: Breadth first search, depth first search, and some sort of A* search.
Before choosing one, I started writing the way that I would retrieve links from the media wiki api. I had to check for a field that was returned to ensure I got all the links for a page since the limit for a response was 500. I made sure to put them in a set to make quick look ups and take care of any duplicates. 
So now the process would be: get links -> parse them -> check if the destination is in the set of links -> if not start the process again with a recursive call to get the links of the links on the page you just checked. This led to an eternal depth first approach on the first page of every first page. So I implemented a way to keep track of the depth and reset to search the next page breadth wise. This was the start of my journey to callback hell. 
I spent a lot of time trying to make node synchronous which is an easy way to find yourself losing your mind. So after attempting to do async mutual recursion, I got to the point of finding the destination page, but I had to slow down my api calls because I was getting blocked by media wiki. So I decided to write a simple web scraper script to pull the links myself, while also putting some measures to slow down the concurrent requests.
There was still the problem of stopping. It would find the destination page but my wikiracer was not satisfied, it just kept searching. Some suggested just ```shell process.exit()``` however this isn’t just a script running. I need to get the response to the server.

### Python

I started reading more about asynchronous coding. In the end, I decided to pivot to python. I thought implementing this synchronously with a language I have more experience with would make the implementation of the async solution easier. I found asyncio, a python library for making python asynchronous, which made me hopeful of my approach.

The python solution I decided on was a variation of A* search. I would use a priority queue to store the next pages to search. The priority (heuristic) would be the amount of links a page had similar to the destination page. This has its immediate drawbacks being you have to get the links for all the pages you retrieved before you can give a priority, but it does give you an idea to start searching in a direction with some context. For short paths this worked well, but the amount of time to get the links was a major speed bump in performance and finding distant pages was taking too long.

I started doing more reading on the benefits of asynchronous code. I read a great example of a chess player that I will link below in the resources section. Basically while my wikiracer is waiting for the links to come from the api (an IO operation) it could be doing some other operation like checking the links it already has received. 

### Python async 1

Async io has good documentation and there are a lot of great resources for learning about async io implementations in python. I had to decouple the process of fetching links(titles) from the process of checking if the destination was on a page. While async io has an awaitable priority queue, I did not want to hinder the process of getting links by having to get links before determining priority. I wanted them to just keep fetching links. I track a couple states: the page titles with the links on that page, the previous page from which a page linked from, all the pages we have seen/checked, and a queue keeping track of all the pages we have yet to check.

The queue is passing the items that were just fetched from the media wiki api to the search worker so it can immediately check if the destination link is on that page. I can see the wikiracer getting links and checking those links. Still I am not fully taking advantage of the full power of running concurrent requests as I came to find out. I was only ever waiting on one request at a time. I wanted to be able to make multiple requests at a time and wait for them to return. I need to spin up multiple instances of my fetch links worker to be able to process the titles to fetch queue faster. 

### Python async 2 - final

I decided I need to have two separate queues so the workers can handle jobs without necessarily waiting on the other to finish. The two queues are like the backlog for each type of worker. Each type of worker is both a producer of work and a consumer of work for each type of queue. 
7 fetch workers *consume* titles from the *fetch* queue and *produce* links to the *titles to visit* queue.
1 search worker *consumes* links from the *titles to visit* queue and *produces* titles to fetch to the *fetch* queue. 
 
The search is faster but going back to the media wiki api call from earlier (that gets the pages that link to a page), it would allow me to search backwards from the destination to the source. Therefore, I could search forward and backward and check if we ever cross paths. That would allow me to search even faster by increasing the items we are looking for each time a call is made on either side. That would be the future implementation for this wikiracer. 

## How long you spent on each part:
* Nodejs version - 				    a day and a half
* Python synchronous version - 			    one day
* Python asynchronous version - 			    two days
* Optimizing async, error checking, dockerizing -	    one day 

## Resources

### asyncio
[Stack overflow - how does asyncio work](https://stackoverflow.com/questions/49005651/how-does-asyncio-actually-work/51116910#51116910)
[Detailed article - chess example is here](https://realpython.com/async-io-python/#async-io-explained)

[asyncio docs - current version in project requires python 3.7](https://docs.python.org/3/library/asyncio.html)


### aiohttps
[aiohttps tutorial](https://aiohttp-demos.readthedocs.io/en/latest/preparations.html#project-structure)

