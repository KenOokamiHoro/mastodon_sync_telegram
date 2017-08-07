import config
from mastodon import Mastodon

if __name__ == "__main__":

    instance = input("Which instance ? ")
    username = input("Username ? ")
    password = input("Password ? ")
    app_name = 'mastodon_sync_telegram_dev'

    # Register app - only once!
    client_id, client_secret = Mastodon.create_app(
        client_name=app_name,
        api_base_url=instance,
    )

    test_instance = Mastodon(
        client_id=client_id,
        client_secret=client_secret,
        api_base_url=instance
    )

    user_token = test_instance.log_in(
        username=username, password=password
    )

    template = {
        'instance':instance,
        'client_id': client_id,
        'client_secret': client_secret,
        'user_token': user_token}

    print(template)
