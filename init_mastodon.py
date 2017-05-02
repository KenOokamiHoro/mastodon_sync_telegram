import config
from mastodon import Mastodon

if __name__=="__main__":
    
    # Register app - only once!
    Mastodon.create_app(
        'mastodon_sync_telegram',
        api_base_url=config.mastodon_instance,
        to_file = 'pytooter_clientcred.secret'
    )
