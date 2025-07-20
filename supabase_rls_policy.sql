
ALTER TABLE swipes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous inserts on swipes" ON swipes
    FOR INSERT 
    TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous selects on swipes" ON swipes
    FOR SELECT 
    TO anon
    USING (true);
