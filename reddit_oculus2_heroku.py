import asyncpraw
import asyncio
import datetime as dt
import os


client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
refresh_token = os.getenv("refresh_token")

user_agent = "Linux:oculus_async_bot_oauth:0.03 (by /u/lukeg55)"



def comment_is_top_level(comment, submission):
    return comment.parent_id.endswith(submission.id)


class HPFModeUpdater:
    def __init__(self):
        self.start_time = dt.time(hour=14, minute=59, second=30)
        self.end_time = (dt.datetime.combine(dt.date.today(), self.start_time) + dt.timedelta(minutes=2)).time()
        
    def set_new_time(self, new_start_time):
        self.start_time = (dt.datetime.combine(dt.date.today(), new_start_time) - dt.timedelta(minutes=1)).time()
        self.end_time = (dt.datetime.combine(dt.date.today(), self.start_time) + dt.timedelta(minutes=2)).time()
                      
    def get_hpf_mode_range(self):
        return (self.start_time, self.end_time)
    

async def high_performance_mode_switcher (reddit, offer_task, submitter, offer_task_in_high_performance_mode = False):
    time_updater = HPFModeUpdater()
    while True:
        now = dt.datetime.now()
        start, stop = time_updater.get_hpf_mode_range()
        high_performance_mode_time = (start <= now.time() <= stop)
        if high_performance_mode_time ^ offer_task_in_high_performance_mode:
            print (f"Cancelled offer_task at {dt.datetime.now()}")
            offer_task.cancel()
            try:
                await offer_task
            except asyncio.CancelledError:
                pass
            offer_task_in_high_performance_mode = not offer_task_in_high_performance_mode
            print (f"Restarting offer_task at {dt.datetime.now()}, high performance mode = {offer_task_in_high_performance_mode}")
            offer_task = asyncio.create_task(submitter.submit_offer(reddit, offer_task_in_high_performance_mode, time_updater))
        await asyncio.sleep(25)

class Submitter:
    DEFAULT_TEXT = """# Global (non-US) referral:
                    
[https://www.oculus.com/referrals/link/lukeg55/](https://www.oculus.com/referrals/link/lukeg55/)
    
Hi, non-US referral. Even outside of US, we don't have to be friends on Facebook for my referral to work. Simply use this link. I have already successuflly referred people from EU, UK, UKR, Canada, AUS. DM me if you still need the link on Facebook/Messenger."""
    
    def __init__(self, subreddit_name, thread_title, text=DEFAULT_TEXT):
        self.submitted_ids = set()
        self.subreddit_name = subreddit_name
        self.thread_titile = thread_title
        self.text = text

    async def submit_offer(self, reddit, highPerformanceMode = False, time_updater = None):
        subreddit = await reddit.subreddit(self.subreddit_name)

        mode = { "pause_after" : 0} if highPerformanceMode else {}

        async for submission in subreddit.stream.submissions(**mode):
            now = dt.datetime.now()

            print(now, end=' ')
            if submission is not None:
                print (submission.title)
            else:
                print()

            if submission is None:
                continue
            if self.thread_titile in submission.title:
                created = dt.datetime.fromtimestamp(submission.created)
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!Found daily megathread at {now}, created at {created}")
                if now - created < dt.timedelta(hours=1,minutes=30) and \
                        submission.id not in self.submitted_ids:
                    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!Adding a message to {submission.url} at {dt.datetime.now()}")
                    await submission.reply(self.text)
                    self.submitted_ids.add(submission.id)
                    if time_updater is not None: time_updater.set_new_time(now)
                    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!! submission added at {dt.datetime.now()}")

async def restarter (task, *args, **kwargs):
    while True:
        try:
            await task (*args, **kwargs)
        except asyncio.CancelledError as e:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print (f"Task failed, restarting, exception: {e}")
            await asyncio.sleep(5*60)


async def amain():
    async with asyncpraw.Reddit(refresh_token=refresh_token,
                                client_id=client_id,
                                client_secret=client_secret,
                                user_agent=user_agent) as reddit:

        oculus_quest_reddit = Submitter("OculusQuest", "Daily Referral Megathread", """Region: Worldwide/global/non-US (EU, UK, AUS, CA, UKR, ZA, MEX, ...)

Referral Link : https://www.oculus.com/referrals/link/lukeg55/""")
        oculus_reddit = Submitter("Oculus", "[Monthly] Referral Sharing Thread")
        new_daily_thread = asyncio.create_task(oculus_quest_reddit.submit_offer(reddit))
        monthly_thread = asyncio.create_task(oculus_reddit.submit_offer(reddit))
        high_performance_mode = asyncio.create_task(high_performance_mode_switcher(reddit, new_daily_thread, oculus_quest_reddit))

        await high_performance_mode
        await monthly_thread


if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(restarter(amain))
    except:
        print("failing")
