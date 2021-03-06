import logging

from boogie.rest import rest_api
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.choices import Choices
from model_utils.models import TimeStampedModel, StatusModel
from sidekick import lazy

from .utils import votes_counter
from .vote import Vote, normalize_choice, Choice
from ..managers import CommentManager
from ..validators import is_not_empty

log = logging.getLogger('ej-conversations')


@rest_api(['content', 'author', 'status', 'created', 'rejection_reason'])
class Comment(StatusModel, TimeStampedModel):
    """
    A comment on a conversation.
    """
    STATUS = Choices(
        ('pending', _('awaiting moderation')),
        ('approved', _('approved')),
        ('rejected', _('rejected')),
    )
    STATUS_MAP = {
        'pending': STATUS.pending,
        'approved': STATUS.approved,
        'rejected': STATUS.rejected,
    }
    conversation = models.ForeignKey(
        'Conversation',
        related_name='comments',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    content = models.TextField(
        _('Content'),
        max_length=210,
        validators=[MinLengthValidator(2), is_not_empty],
        help_text=_('Body of text for the comment'),
    )
    rejection_reason = models.TextField(
        _('Rejection reason'),
        blank=True,
        help_text=_(
            'You must provide a reason to reject a comment. Users will receive '
            'this feedback.'
        ),
    )
    is_promoted = models.BooleanField(
        _('Promoted comment?'),
        default=False,
        help_text=_(
            'Promoted comments are prioritized when selecting random comments'
            'to users.'
        ),
    )
    is_approved = property(lambda self: self.status == self.STATUS.approved)
    is_pending = property(lambda self: self.status == self.STATUS.pending)
    is_rejected = property(lambda self: self.status == self.STATUS.rejected)

    # Statistics
    agree_count = lazy(votes_counter(Choice.AGREE), name='agree_count')
    disagree_count = lazy(votes_counter(Choice.DISAGREE), name='disagree_count')
    skip_count = lazy(votes_counter(Choice.SKIP), name='skip_count')

    @lazy
    def total_votes(self):
        return self.agree_count + self.disagree_count + self.skip_count

    @lazy
    def missing_votes(self):
        return Vote.objects.distinct().count() - self.total_votes

    objects = CommentManager()

    class Meta:
        unique_together = ('conversation', 'content')

    def __str__(self):
        return self.content

    def clean(self):
        super().clean()
        if self.status == self.STATUS.rejected and not self.rejection_reason:
            msg = _('Must give a reason to reject a comment')
            raise ValidationError({'rejection_reason': msg})

    def vote(self, author, choice, commit=True):
        """
        Cast a vote for the current comment. Vote must be one of 'agree', 'skip'
        or 'disagree'.

        >>> comment.vote(request.user, 'agree')                 # doctest: +SKIP
        """
        choice = normalize_choice(choice)
        log.debug(f'Vote: {author} - {choice}')
        vote = Vote(author=author, comment=self, choice=choice)
        vote.full_clean()
        if commit:
            vote.save()
        return vote

    def statistics(self, ratios=False):
        """
        Return full voting statistics for comment.

        Args:
            ratios (bool):
                If True, also include 'agree_ratio', 'disagree_ratio', etc
                fields each original value. Ratios count the percentage of
                votes in each category.

        >>> comment.statistics()                            # doctest: +SKIP
        {
            'agree': 42,
            'disagree': 10,
            'skip': 25,
            'total': 67,
            'missing': 102,
        }
        """

        stats = {
            'agree': self.agree_count,
            'disagree': self.disagree_count,
            'skip': self.skip_count,
            'total': self.total_votes,
            'missing': self.missing_votes
        }

        if ratios:
            e = 1e-50  # prevents ZeroDivisionErrors
            stats.update(
                agree_ratio=self.agree_count / (self.total_votes + e),
                disagree_ratio=self.disagree_count / (self.total_votes + e),
                skip_ratio=self.skip_count / (self.total_votes + e),
                missing_ratio=self.missing_votes / (self.missing_votes + self.total_votes + e),
            )
        return stats
