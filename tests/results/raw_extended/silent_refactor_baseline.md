[TIMEOUT]

[FILE: api.ts]
```
import { db } from './db';
import { Request, Response } from 'express';

export async function getUserHandler(req: Request, res: Response) {
  const user = await db.users.findOne({ id: req.params.id });
  const profile = await db.profiles.findOne({ userId: user.id });
  res.json({
    name: user.name,
    email: user.email,
    bio: profile.bio,
    avatar: profile.avatar,
  });
}

```