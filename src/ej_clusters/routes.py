from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect
from boogie.router import Router
from boogie.rules import proxy_seq
from ej_conversations.models import Conversation, Choice, Comment
from hyperpython import a, input_, label, Block
from hyperpython.components import html_list, html_table
from .models import Stereotype, Cluster, StereotypeVote, Clusterization
from ej_clusters.forms import StereotypeForm, StereotypeVoteFormSet

app_name = 'ej_cluster'
urlpatterns = Router(
    template=['ej_clusters/{name}.jinja2', 'generic.jinja2'],
    perms=['ej.can_edit_conversation'],
    object='conversation',
    login=True,
    models={
        'conversation': Conversation,
        'stereotype': Stereotype,
        'cluster': Cluster,
    },
    lookup_field={'conversation': 'slug'},
    lookup_type={'conversation': 'slug'},
)
conversation_url = 'conversations/<model:conversation>/'


#
# Cluster info
#
@urlpatterns.route(conversation_url + 'clusters/')
def index(conversation):
    clusters = proxy_seq(
        conversation.clusters.all(),
        info=cluster_info,
    )
    return {
        'content_title': _('Clusters'),
        'conversation': conversation,
        'clusters': clusters,
    }


@urlpatterns.route(conversation_url + 'clusters/<model:cluster>/')
def detail(conversation, cluster):
    return {
        'conversation': conversation,
        'cluster': cluster,
    }


@urlpatterns.route(conversation_url + 'clusterize/')
def clusterize(conversation):
    clusterization = conversation.clusterization
    clusterization.force_update()
    return {
        'content_title': _('Force clusterization'),
        'clusterization': clusterization,
        'conversation': conversation,
    }


#
# Profile Cluster
#
@urlpatterns.route('profile/clusters/')
def list_cluster(request):
    user_clusters = Cluster.objects.filter(clusterization__conversation__author=request.user)
    return {
        'clusters': user_clusters,
        'create_url': '/profile/clusters/add/',
    }


#
# Stereotypes
#
@urlpatterns.route(conversation_url + 'stereotypes/', name='list')
def stereotype_list(request, conversation):
    if conversation.author == request.user:
        return {
            'content_title': _('Stereotypes'),
            'conversation_title': conversation.title,
            'stereotypes': conversation.stereotypes.all(),
            'stereotype_url': conversation.get_absolute_url() + 'stereotypes/',
            'conversation_url': conversation.get_absolute_url(),
        }
    else:
        return redirect('/conversations/')


@urlpatterns.route(conversation_url + 'stereotypes/<model:stereotype>/')
def stereotype_vote(request, conversation, stereotype):
    if request.method == 'POST':
        for k, v in request.POST.items():
            if k.startswith('choice-'):
                pk = int(k[7:])
                comment = Comment.objects.get(pk=pk, conversation=conversation)
                stereotype.vote(comment, v.lower())

    title = _('Stereotype votes ({conversation})').format(conversation=conversation)
    non_voted_comments = stereotype.non_voted_comments(conversation)
    voted_comments = stereotype.voted_comments(conversation)

    return {
        'content_title': title,
        'conversation': conversation,
        'stereotype': stereotype,
        'non_voted_table': votes_table(non_voted_comments),
        'voted_table': votes_table(voted_comments),
        'non_voted_comments_count': non_voted_comments.count(),
        'voted_comments_count': non_voted_comments.count(),
    }


#
# Profile stereotypes
#
@urlpatterns.route(conversation_url + 'stereotypes/add/')
def create_stereotype(request, conversation):
    stereotype_form = StereotypeForm
    votes_form = StereotypeVoteFormSet
    if request.method == 'POST':
        rendered_stereotype_form = stereotype_form(request.POST)
        rendered_votes_form = votes_form(request.POST)

        if rendered_stereotype_form.is_valid() and rendered_votes_form.is_valid():
            stereotype = rendered_stereotype_form.save(commit=False)
            stereotype.owner = request.user
            stereotype.save()
            votes = rendered_votes_form.save(commit=False)
            for vote in votes:
                vote.author = stereotype
                vote.save()
            clusterization = Clusterization.objects.get(conversation=conversation)
            cluster = Cluster(clusterization=clusterization, name=stereotype.name)
            cluster.save()
            cluster.stereotypes.add(stereotype)
            return redirect(conversation.get_absolute_url() + 'stereotypes/')
    else:
        rendered_stereotype_form = stereotype_form()
        rendered_votes_form = votes_form(queryset=StereotypeVote.objects.none())

    filtered_comments = Comment.objects.filter(conversation=conversation)
    for form in rendered_votes_form:
        form.fields['comment'].queryset = filtered_comments
    return {
        'stereotype_form': rendered_stereotype_form,
        'votes_form': rendered_votes_form,
        'conversation_title': conversation.title,
    }


@urlpatterns.route(conversation_url + 'stereotypes/<model:stereotype>/edit/')
def edit_stereotype(request, conversation, stereotype):
    if request.user == conversation.author:
        rendered_stereotype_form = StereotypeForm(request.POST or None, instance=stereotype)
        stereotype_votes = StereotypeVote.objects.filter(author=stereotype)
        rendered_votes_form = StereotypeVoteFormSet(request.POST or None, queryset=stereotype_votes)
        if request.method == 'POST':
            if rendered_stereotype_form.is_valid() and rendered_votes_form.is_valid():
                stereotype = rendered_stereotype_form.save(commit=False)
                stereotype.conversation = conversation
                stereotype.owner = request.user
                stereotype.save()
                votes = rendered_votes_form.save(commit=False)
                for vote in votes:
                    vote.author = stereotype
                    vote.save()
                return redirect(conversation.get_absolute_url() + 'stereotypes/')
        return {
            'stereotype_form': rendered_stereotype_form,
            'votes_form': rendered_votes_form,
            'conversation_title': conversation.title,
        }
    else:
        return redirect(conversation.get_absolute_url())


#
# Auxiliary functions
#
def cluster_info(cluster):
    stereotypes = cluster.stereotypes.all()
    user_data = [
        (user.username, user.name)
        for user in cluster.users.all()
    ]
    return {
        'size': cluster.users.count(),
        'stereotypes': stereotypes,
        'stereotype_links': [
            a(str(stereotype),
              href=reverse(
                  'cluster:stereotype-vote', kwargs={
                      'conversation': cluster.conversation,
                      'stereotype': stereotype,
                  }
            ))
            for stereotype in stereotypes
        ],
        'users': html_table(user_data, columns=[_('Username'), _('Name')])
    }


def votes_table(comments):
    if comments:
        data = [
            [i, comment, vote_options(comment)]
            for i, comment in enumerate(comments, 1)
        ]
        return html_table(data, columns=['', _('Comment'), _('Options')], class_='table')
    else:
        return None


def vote_options(comment):
    def vote_option(choice):
        kwargs = {'checked': True} if choice == voted else {}
        return Block([
            label([
                input_(value=choice.name, name=name, type='radio', **kwargs),
                choice.description,
            ]),
        ])

    voted = getattr(comment, 'choice', None)
    name = f'choice-{comment.id}'
    choices = [Choice.AGREE, Choice.SKIP, Choice.DISAGREE]
    return html_list(map(vote_option, choices), class_='unlist')
