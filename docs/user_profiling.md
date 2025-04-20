# User Profiling Process

This document explains the user profiling process in the HotLabel platform, including how user expertise is inferred, how tasks are matched to users, and how the staircase model works for task distribution.

## Privacy-First Approach

The HotLabel platform uses a privacy-first approach to user profiling:

1. **Anonymized Sessions**: All user activity is initially tracked anonymously through browser sessions
2. **No Personal Information**: No personally identifiable information (PII) is collected unless the user opts in
3. **Data Minimization**: Only the minimum necessary data is collected for task matching
4. **Data Retention**: Session data is automatically purged after a configurable period
5. **Explicit Consent**: All profiling activities require explicit user consent

## User Profiling Process

The user profiling process involves several steps:

### 1. Session Tracking

When a user visits a publisher website using the HotLabel SDK, an anonymous session is created. During this session, the following signals are collected:

- **Browser Information**: Language, user agent, screen resolution
- **Website Category**: Topic category of the current website
- **Interaction Patterns**: Time spent on pages, scroll behavior, clicks

### 2. Expertise Inference

The ProfilerService processes these signals to infer:

- **Language Proficiency**: Primary language and additional languages
- **Domain Knowledge**: Areas of expertise based on website categories visited
- **Skill Level**: Based on task history and performance

### 3. Profile Creation (Optional)

Users can opt in to create a profile, which allows:

- Persistent tracking across sessions
- Accumulation of expertise metrics
- Access to more complex or rewarding tasks
- Personalized task recommendations

## The Staircase Model

The task compatibility system uses a "staircase model" to distribute tasks based on user expertise:

### Task Complexity Levels

Tasks are categorized into complexity levels:

- **Level 0**: Entry-level tasks with minimal domain knowledge required
- **Level 1**: Basic tasks requiring some understanding of the domain
- **Level 2**: Intermediate tasks requiring good domain knowledge
- **Level 3**: Advanced tasks requiring strong domain knowledge
- **Level 4**: Expert tasks requiring deep domain expertise

### User Expertise Levels

Users are categorized into expertise levels based on:

- Number of tasks completed
- Success rate
- Quality scores
- Domain-specific performance

### Progression Rules

The staircase model dictates how users progress through task complexity:

1. **Entry Point**: New users start with Level 0 tasks
2. **Advancement**: Users advance to higher complexity tasks after demonstrating competence
3. **Minimum Requirements**:
   - Level 1: 10+ tasks completed with >80% success rate
   - Level 2: 50+ tasks completed with >85% success rate
   - Level 3: 100+ tasks completed with >90% success rate
   - Level 4: 250+ tasks completed with >95% success rate
4. **Matching Algorithm**: Users are matched with tasks at or below their expertise level

### Example Progression

```
Level 4: Expert Tasks           |            ┌────┐
                               |            │    │
Level 3: Advanced Tasks        |        ┌───┴────┤
                               |        │         │
Level 2: Intermediate Tasks    |    ┌───┴─────────┤
                               |    │             │
Level 1: Basic Tasks           |┌───┴─────────────┤
                               |│                 │
Level 0: Entry Tasks           |└─────────────────┘
                               +--------------------
                                  Task History
```

## Task Distribution Process

The TaskCompatibilityService handles the task distribution process:

1. **Signal Collection**: Gathers user session data and expertise metrics
2. **Expertise Evaluation**: Determines the user's expertise level
3. **Task Matching**: Finds tasks that match the user's expertise level and language
4. **Prioritization**: Applies business rules for prioritizing tasks
5. **Distribution**: Sends matched tasks to the user

## Language Matching

Tasks are matched to users based on language proficiency:

1. **Primary Language**: Tasks in the user's primary language are prioritized
2. **Secondary Languages**: Tasks in languages where the user has demonstrated proficiency
3. **Language Complexity**: Task language complexity is matched to the user's proficiency level

## Quality Feedback Loop

Task completion data is fed back into the profiling system:

1. **Performance Tracking**: Success rates and quality scores are tracked
2. **Profile Updates**: User expertise profiles are updated based on performance
3. **Task Adjustment**: Future task matching is refined based on performance
4. **Level Adjustments**: Users may move up or down levels based on consistent performance

## Statistical Safeguards

To ensure quality, several statistical safeguards are implemented:

1. **Confidence Scores**: Each expertise inference has a confidence score
2. **Validation Tasks**: Periodic validation tasks verify user expertise
3. **Consistency Checks**: Unusual patterns trigger additional verification
4. **Golden Set**: Pre-labeled samples validate user performance
