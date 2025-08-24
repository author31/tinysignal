from ..repositories.cluster import ClusterRepository
from ..models.cluster import ClusterDisplayModel
from . import cluster

cluster_repo = ClusterRepository()

def get_telegram_hot_news() -> dict:
    """Get hot news clusters formatted for Telegram inline buttons"""
    clusters = cluster_repo.get_clusters()
    # if len(clusters) == 0:
    #     return {
    #         "text": "There aren't any hot news recently.",
    #         "reply_markup": {"inline_keyboard": []}
    #     }
    
    cluster_data = cluster.get_cluster_display_data()
    return format_clusters_for_inline_buttons(cluster_data)

def format_clusters_for_inline_buttons(clusters: list[ClusterDisplayModel]) -> dict:
    """Format cluster data for Telegram inline keyboard"""
    if not clusters:
        return {
            "text": "There aren't any hot news recently.",
            "reply_markup": {"inline_keyboard": []}
        }
    
    inline_keyboard = []
    for cluster in clusters:
        button = {
            "text": cluster.title,
            "callback_data": f"cluster_{cluster.cluster_idx}"
        }
        inline_keyboard.append([button])
    
    return {
        "text": "🔥 Hot News Clusters:",
        "reply_markup": {"inline_keyboard": inline_keyboard}
    }

def get_telegram_cluster_posts(cluster_idx: int) -> dict:
    """Get posts for a specific cluster formatted for Telegram inline buttons"""
    posts = cluster_repo.get_posts_by_cluster_idx(cluster_idx, limit=10)
    
    if not posts:
        return {
            "text": "No posts found for this cluster.",
            "reply_markup": {"inline_keyboard": []}
        }
    
    # Create inline keyboard with posts
    inline_keyboard = []
    for post in posts:
        button_text = post["title"][:50] + "..." if len(post["title"]) > 50 else post["title"]
        button = {
            "text": button_text,
            "url": post["url"]
        }
        inline_keyboard.append([button])
    
    # Add back button
    inline_keyboard.append([
        {"text": "🔙 Back to clusters", "callback_data": "back_to_clusters"}
    ])
    
    return {
        "text": f"📰 Posts in cluster:",
        "reply_markup": {"inline_keyboard": inline_keyboard}
    }

def handle_telegram_callback(callback_data: str) -> dict:
    """Handle Telegram callback queries"""
    if callback_data.startswith("cluster_"):
        cluster_idx = int(callback_data.split("_")[1])
        return get_telegram_cluster_posts(cluster_idx)
    elif callback_data == "back_to_clusters":
        return get_telegram_hot_news()
    else:
        return {
            "text": "Unknown command.",
            "reply_markup": {"inline_keyboard": []}
        }
