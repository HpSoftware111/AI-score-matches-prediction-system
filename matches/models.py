from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import datetime


class Team(models.Model):
    """Team model for storing sport teams"""
    name = models.CharField(max_length=100, unique=True)
    logo_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Match(models.Model):
    """Match model for storing fixtures with probabilities and odds"""
    team_a = models.ForeignKey(
        Team, 
        related_name="home_matches", 
        on_delete=models.CASCADE,
        verbose_name="Team A (Home)"
    )
    team_b = models.ForeignKey(
        Team, 
        related_name="away_matches", 
        on_delete=models.CASCADE,
        verbose_name="Team B (Away)"
    )
    date = models.DateTimeField(verbose_name="Match Date")
    prob_a = models.FloatField(
        help_text="Probability for Team A winning (e.g., 0.29 = 29%)",
        verbose_name="Team A Probability"
    )
    prob_b = models.FloatField(
        help_text="Probability for Team B winning (e.g., 0.46 = 46%)",
        verbose_name="Team B Probability"
    )
    odds_a = models.FloatField(
        help_text="Sportsbook odds for Team A",
        verbose_name="Team A Odds"
    )
    odds_b = models.FloatField(
        help_text="Sportsbook odds for Team B",
        verbose_name="Team B Odds"
    )
    draw_prob = models.FloatField(
        default=0.0,
        help_text="Probability of a draw (e.g., 0.25 = 25%)",
        verbose_name="Draw Probability"
    )
    week_number = models.IntegerField(
        blank=True,
        null=True,
        help_text="Week number of the year (1-53)",
        verbose_name="Week Number"
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Country of the league (e.g., England, Spain)",
        verbose_name="Country"
    )
    game_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="League/competition name (e.g., EPL, La Liga)",
        verbose_name="Game Title"
    )
    actual_result = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('3', 'Team A Win'), ('1', 'Draw'), ('0', 'Team B Win')],
        help_text="Actual match result: 3=Team A, 1=Draw, 0=Team B",
        verbose_name="Actual Result"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.team_a} vs {self.team_b} - {self.date.strftime('%Y-%m-%d %H:%M')}"

    def get_absolute_url(self):
        return reverse('matches:match_detail', kwargs={'pk': self.pk})

    def clean(self):
        """Validate that team_a and team_b are different"""
        if self.team_a_id and self.team_b_id and self.team_a_id == self.team_b_id:
            raise ValidationError({
                'team_b': 'Team A and Team B must be different teams.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation and calculate week_number"""
        # Calculate week_number from date if not set
        if self.date and not self.week_number:
            self.week_number = self.calculate_week_number()
        self.full_clean()
        super().save(*args, **kwargs)
    
    def calculate_week_number(self):
        """Calculate ISO week number from date"""
        if self.date:
            return self.date.isocalendar()[1]
        return None

    @property
    def prob_a_percent(self):
        """Return probability as percentage"""
        return round(self.prob_a * 100, 2)

    @property
    def prob_b_percent(self):
        """Return probability as percentage"""
        return round(self.prob_b * 100, 2)

    @property
    def draw_prob_percent(self):
        """Return draw probability as percentage"""
        return round(self.draw_prob * 100, 2)

    @property
    def implied_prob_a(self):
        """Calculate implied probability from odds"""
        if self.odds_a > 0:
            return 1 / self.odds_a
        return 0

    @property
    def implied_prob_b(self):
        """Calculate implied probability from odds"""
        if self.odds_b > 0:
            return 1 / self.odds_b
        return 0

