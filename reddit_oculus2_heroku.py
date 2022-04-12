import asyncpraw
import asyncio
import datetime as dt
import os


client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
refresh_token = os.getenv("refresh_token")

user_agent = "Linux:oculus_async_bot_oauth:0.01 (by /u/lukeg55)"



def comment_is_top_level(comment, submission):
    return comment.parent_id.endswith(submission.id)




async def high_performance_mode_switcher (reddit, offer_task, offer_task_in_high_performance_mode = False):
    while True:
        now = dt.datetime.now()
        high_performance_mode_time = (dt.time(hour=14, minute=59, second=30) <= now.time() <= dt.time(hour=15, minute=1, second=30))
        if high_performance_mode_time ^ offer_task_in_high_performance_mode:
            print (f"Cancelled offer_task at {dt.datetime.now()}")
            offer_task.cancel()
            offer_task_in_high_performance_mode = not offer_task_in_high_performance_mode
            print (f"Restarting offer_task at {dt.datetime.now()}, high performance mode = {offer_task_in_high_performance_mode}")
            offer_task = asyncio.create_task(submit_offer(reddit, offer_task_in_high_performance_mode))
        await asyncio.sleep(25)

submitted_ids = set()
async def submit_offer(reddit, highPerformanceMode = False):
    subreddit = await reddit.subreddit("OculusQuest")

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
        if "Daily Referral Megathread" in submission.title:
            created = dt.datetime.fromtimestamp(submission.created)
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!Found daily megathread at {now}, created at {created}")
            if now - created < dt.timedelta(minutes=5) and \
                    submission.id not in submitted_ids:
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!Adding a message to {submission.url} at {dt.datetime.now()}")
                await submission.reply("""# Global (non-US) referral:
                
[https://www.oculus.com/referrals/link/lukeg55/](https://www.oculus.com/referrals/link/lukeg55/)

Hi, non-US referral. Even outside of US, we don't have to be friends on Facebook for my referral to work. Simply use this link. I have already successuflly referred people from EU, UK, UKR, Canada, AUS. DM me if you still need the link on Facebook/Messenger.""")
                submitted_ids.add(submission.id)
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!! submission added at {dt.datetime.now()}")

async def restarter2 (task, *args, **kwargs):
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
        new_daily_thread = asyncio.create_task(submit_offer(reddit))
        high_performance_mode = asyncio.create_task(high_performance_mode_switcher(reddit, new_daily_thread))

        await high_performance_mode


if __name__ == '__main__':
    asyncio.run(restarter2(amain))
